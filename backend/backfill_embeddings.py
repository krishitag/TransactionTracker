"""Fill in summary + embedding for scored transactions that don't have one yet.

Run from backend/:  venv/bin/python backfill_embeddings.py
Use --all to rebuild every row (e.g. after changing the summary format).
"""
import os
import sys

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

from embeddings import build_summary, embed, to_pgvector

BATCH_SIZE = 256

load_dotenv()


def main():
    rebuild_all = "--all" in sys.argv
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    try:
        with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"""
                SELECT r.id, r.risk_score, r.risk_level, r.reasons,
                       t.merchant, t.category, t.amount, t.trans_time, t.cc_num
                  FROM risk_scores r
                  JOIN transactions t ON t.id = r.transaction_id
                 {"" if rebuild_all else "WHERE r.embedding IS NULL"}
                 ORDER BY r.id;
                """
            )
            rows = cur.fetchall()
            print(f"{len(rows)} rows to embed")

            for start in range(0, len(rows), BATCH_SIZE):
                batch = rows[start:start + BATCH_SIZE]
                summaries = [
                    build_summary(r, r["risk_score"], r["risk_level"], r["reasons"]) for r in batch
                ]
                vectors = embed(summaries)
                cur.executemany(
                    "UPDATE risk_scores SET summary = %s, embedding = %s::vector WHERE id = %s;",
                    [(s, to_pgvector(v), r["id"]) for s, v, r in zip(summaries, vectors, batch)],
                )
                print(f"  embedded {start + len(batch)}/{len(rows)}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
