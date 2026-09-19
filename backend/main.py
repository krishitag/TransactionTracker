import os
from datetime import datetime
from typing import Optional

import psycopg2
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

load_dotenv()

app = FastAPI()


class TransactionIn(BaseModel):
    trans_num: str
    cc_num: str
    merchant: str
    category: str
    amount: float
    trans_time: datetime
    cust_lat: float
    cust_long: float
    merch_lat: float
    merch_long: float
    is_fraud: Optional[bool] = None


def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))


@app.post("/transactions")
def create_transaction(txn: TransactionIn):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO transactions
            (trans_num, cc_num, merchant, category, amount, trans_time,
             cust_lat, cust_long, merch_lat, merch_long, is_fraud)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """,
        (
            txn.trans_num, txn.cc_num, txn.merchant, txn.category, txn.amount,
            txn.trans_time, txn.cust_lat, txn.cust_long, txn.merch_lat,
            txn.merch_long, txn.is_fraud,
        ),
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return {"id": new_id, "trans_num": txn.trans_num}
