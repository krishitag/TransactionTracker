import os
from datetime import datetime, timezone
from typing import Optional

import psycopg2
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from psycopg2.extras import Json, RealDictCursor
from pydantic import BaseModel, Field

from scoring import model_version, score_transaction

load_dotenv()

app = FastAPI()

MODEL_VERSION = model_version()


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


def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))


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

            cur.execute(
                """
                INSERT INTO risk_scores
                    (transaction_id, risk_score, risk_level, reasons, contributions, features, model_version)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
                """,
                (
                    new_id, result["risk_score"], result["risk_level"], Json(result["reasons"]),
                    Json(result["contributions"]), Json(result["features"]), MODEL_VERSION,
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
