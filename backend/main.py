import os
from datetime import datetime, timezone
from typing import Literal, Optional

import psycopg2
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from psycopg2.extras import Json, RealDictCursor
from pydantic import BaseModel, Field

from ask import LLMNotConfigured, LLMRateLimited, LLMUnavailable, answer, retrieve
from embeddings import CATEGORY_NAMES, build_summary, embed, get_model, to_pgvector
from scoring import model_version, score_transaction

load_dotenv()

app = FastAPI()

# Browsers only let the dashboard (another origin) read our responses if we allow it.
# Allow just the known frontend origin(s), not "*".
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("FRONTEND_ORIGINS", "http://localhost:3100").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

MODEL_VERSION = model_version()

# Load the embedding model at startup so the first request isn't slow.
get_model()


class TransactionIn(BaseModel):
    trans_num: str
    cc_num: str
    merchant: str
    category: str
    amount: float = Field(ge=0)
    trans_time: datetime
    cust_lat: float = Field(ge=-90, le=90)
    cust_long: float = Field(ge=-180, le=180)
    merch_lat: float = Field(ge=-90, le=90)
    merch_long: float = Field(ge=-180, le=180)
    is_fraud: Optional[bool] = None


class AskIn(BaseModel):
    question: str = Field(min_length=3, max_length=500)


def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))


def read_rows(sql, params=None):
    """Run a read-only query and return rows as dicts."""
    conn = get_connection()
    try:
        with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SET TRANSACTION READ ONLY")
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        conn.close()


# Shape of one transaction as the dashboard sees it. Only the last 4 card digits
# ever leave the API: the browser never needs the full card number.
TRANSACTION_COLUMNS = """
    t.id, t.trans_num, right(t.cc_num, 4) AS card_last4, t.merchant, t.category,
    t.amount::float AS amount, t.trans_time, t.is_fraud,
    r.risk_score, r.risk_level, r.reasons, r.features, r.model_version
"""


def present_transaction(row):
    row = dict(row)
    row.pop("total", None)
    row["category_name"] = CATEGORY_NAMES.get(row["category"], row["category"])
    return row


def clean_transaction(txn):
    # Sparkov prefixes every merchant name with "fraud_"; it isn't a fraud signal,
    # so strip it once here and everything downstream sees clean names.
    txn.merchant = txn.merchant.removeprefix("fraud_")
    # Store times as naive UTC so incoming and stored times always compare cleanly.
    if txn.trans_time.tzinfo is not None:
        txn.trans_time = txn.trans_time.astimezone(timezone.utc).replace(tzinfo=None)
    return txn


# Only the history the features need: the card's last hour (velocity) plus its
# earliest earlier visit to this merchant (first-time-merchant). Gives the same
# features as the full history without loading years of rows.
HISTORY_SQL = """
    (SELECT id, cc_num, merchant, amount, trans_time, cust_lat, cust_long, merch_lat, merch_long
       FROM transactions
      WHERE cc_num = %(cc_num)s AND id <> %(id)s
        AND trans_time BETWEEN %(trans_time)s - INTERVAL '1 hour' AND %(trans_time)s)
    UNION
    (SELECT id, cc_num, merchant, amount, trans_time, cust_lat, cust_long, merch_lat, merch_long
       FROM transactions
      WHERE cc_num = %(cc_num)s AND id <> %(id)s
        AND merchant = %(merchant)s AND trans_time <= %(trans_time)s
      ORDER BY trans_time
      LIMIT 1)
"""


def to_scoring_row(row):
    """Map API/database column names to the Sparkov names the model was trained on."""
    return {
        "cc_num": row["cc_num"],
        "merchant": row["merchant"],
        "amt": float(row["amount"]),
        "trans_date_trans_time": row["trans_time"],
        "lat": row["cust_lat"],
        "long": row["cust_long"],
        "merch_lat": row["merch_lat"],
        "merch_long": row["merch_long"],
    }


@app.post("/transactions", status_code=201)
def create_transaction(txn: TransactionIn):
    txn = clean_transaction(txn)
    conn = get_connection()
    try:
        # Everything below is one database transaction: if scoring fails, the
        # insert is rolled back too, so no transaction is ever left unscored.
        with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO transactions
                    (trans_num, cc_num, merchant, category, amount, trans_time,
                     cust_lat, cust_long, merch_lat, merch_long, is_fraud)
                VALUES (%(trans_num)s, %(cc_num)s, %(merchant)s, %(category)s, %(amount)s,
                        %(trans_time)s, %(cust_lat)s, %(cust_long)s, %(merch_lat)s,
                        %(merch_long)s, %(is_fraud)s)
                ON CONFLICT (trans_num) DO NOTHING
                RETURNING id;
                """,
                txn.model_dump(),
            )
            inserted = cur.fetchone()
            if inserted is None:
                raise HTTPException(status_code=409, detail=f"Transaction {txn.trans_num} already exists")
            new_id = inserted["id"]

            cur.execute(
                HISTORY_SQL,
                {"id": new_id, "cc_num": txn.cc_num, "merchant": txn.merchant, "trans_time": txn.trans_time},
            )
            history = [to_scoring_row(r) for r in cur.fetchall()]

            result = score_transaction(to_scoring_row(txn.model_dump()), history)

            summary = build_summary(
                txn.model_dump(), result["risk_score"], result["risk_level"], result["reasons"]
            )
            embedding = embed([summary])[0]

            cur.execute(
                """
                INSERT INTO risk_scores
                    (transaction_id, risk_score, risk_level, reasons, contributions, features,
                     model_version, summary, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::vector);
                """,
                (
                    new_id, result["risk_score"], result["risk_level"], Json(result["reasons"]),
                    Json(result["contributions"]), Json(result["features"]), MODEL_VERSION,
                    summary, to_pgvector(embedding),
                ),
            )
    finally:
        conn.close()

    return {
        "id": new_id,
        "trans_num": txn.trans_num,
        "risk_score": result["risk_score"],
        "risk_level": result["risk_level"],
        "reasons": result["reasons"],
    }


@app.get("/health")
def health():
    """Liveness check for the host (Render pings it). No database call, so it stays cheap."""
    return {"status": "ok", "model_version": MODEL_VERSION}


@app.get("/stats")
def stats():
    row = read_rows(
        """
        SELECT count(*)                                          AS total,
               count(*) FILTER (WHERE r.risk_level = 'high')     AS high,
               count(*) FILTER (WHERE r.risk_level = 'medium')   AS medium,
               count(*) FILTER (WHERE r.risk_level = 'low')      AS low,
               coalesce(sum(t.amount) FILTER (WHERE r.risk_level = 'high'), 0)::float   AS high_risk_amount,
               coalesce(sum(t.amount) FILTER (WHERE r.risk_level = 'medium'), 0)::float AS medium_risk_amount,
               coalesce(sum(t.amount) FILTER (WHERE r.risk_level = 'low'), 0)::float    AS low_risk_amount,
               coalesce(sum(t.amount), 0)::float                  AS total_amount
          FROM transactions t
          JOIN risk_scores r ON r.transaction_id = t.id
        """
    )[0]
    return {**row, "model_version": MODEL_VERSION}


@app.get("/transactions")
def list_transactions(
    risk_level: Optional[Literal["high", "medium", "low"]] = None,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    # count(*) OVER () adds the total matching rows to every row, so one query
    # gives both the page and the number of pages.
    rows = read_rows(
        f"""
        SELECT {TRANSACTION_COLUMNS}, count(*) OVER () AS total
          FROM transactions t
          JOIN risk_scores r ON r.transaction_id = t.id
         WHERE (%(risk_level)s::text IS NULL OR r.risk_level = %(risk_level)s::text)
         ORDER BY t.trans_time DESC, t.id DESC
         LIMIT %(limit)s OFFSET %(offset)s
        """,
        {"risk_level": risk_level, "limit": limit, "offset": offset},
    )
    total = rows[0]["total"] if rows else 0
    return {"total": total, "limit": limit, "offset": offset,
            "items": [present_transaction(r) for r in rows]}


@app.get("/transactions/{transaction_id}")
def get_transaction(transaction_id: int):
    rows = read_rows(
        f"""
        SELECT {TRANSACTION_COLUMNS}
          FROM transactions t
          JOIN risk_scores r ON r.transaction_id = t.id
         WHERE t.id = %(id)s
        """,
        {"id": transaction_id},
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")
    return present_transaction(rows[0])


@app.post("/ask")
def ask(body: AskIn):
    # Read what we need, then close the connection before calling the LLM (which takes
    # seconds), so a slow answer never holds a database connection.
    conn = get_connection()
    try:
        with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SET TRANSACTION READ ONLY")
            context = retrieve(cur, body.question)
    finally:
        conn.close()

    try:
        return answer(body.question, context)
    except LLMNotConfigured as e:
        raise HTTPException(status_code=503, detail=f"LLM not configured: {e}")
    except LLMRateLimited as e:
        raise HTTPException(status_code=429, detail=str(e))
    except LLMUnavailable as e:
        raise HTTPException(status_code=502, detail=str(e))
