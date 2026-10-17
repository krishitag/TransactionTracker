-- Useful queries for exploring the Transaction Risk Platform database.
--
-- Run all:  psql "postgresql://risk:risk_dev_password@localhost:5433/risk" -P pager=off -f backend/queries.sql
-- Or copy one query into psql and run it on its own.


-- ============================================================
-- 1. Health checks
-- ============================================================

-- 1a. Table structure (psql shortcut, not SQL).
\d risk_scores

-- 1b. Every scored transaction should have an embedding. "missing" should be 0.
SELECT count(*)                                  AS scored,
       count(*) FILTER (WHERE embedding IS NULL) AS missing_embedding
  FROM risk_scores;


-- ============================================================
-- 2. How good is the model? (compare risk levels with real fraud labels)
-- ============================================================

-- 2a. Risk level vs actual fraud. Precision of a level = actual_fraud / txns.
--     Note: the seed data is fraud-heavy (~8.5%), so precision here looks better
--     than it would at the real 0.58% fraud rate.
SELECT r.risk_level,
       count(*)              AS txns,
       sum(t.is_fraud::int)  AS actual_fraud,
       round(100.0 * sum(t.is_fraud::int) / count(*), 1) AS pct_fraud
  FROM risk_scores r
  JOIN transactions t ON t.id = r.transaction_id
 GROUP BY r.risk_level
 ORDER BY txns DESC;

-- 2b. Recall: of all real fraud, how much did each level catch?
SELECT r.risk_level,
       sum(t.is_fraud::int) AS fraud_caught,
       round(100.0 * sum(t.is_fraud::int) / sum(sum(t.is_fraud::int)) OVER (), 1) AS pct_of_all_fraud
  FROM risk_scores r
  JOIN transactions t ON t.id = r.transaction_id
 GROUP BY r.risk_level
 ORDER BY fraud_caught DESC;


-- ============================================================
-- 3. Where is the risk? (the kind of aggregate /ask will use)
-- ============================================================

-- 3a. Risk by spending category.
SELECT t.category,
       count(*)                                         AS txns,
       count(*) FILTER (WHERE r.risk_level = 'high')    AS high_risk,
       sum(t.is_fraud::int)                             AS actual_fraud,
       round(avg(r.risk_score)::numeric, 3)             AS avg_score
  FROM transactions t
  JOIN risk_scores r ON r.transaction_id = t.id
 GROUP BY t.category
 ORDER BY high_risk DESC;

-- 3b. Merchants with the most high-risk transactions.
SELECT t.merchant,
       count(*)              AS high_risk_txns,
       sum(t.amount)         AS total_amount
  FROM transactions t
  JOIN risk_scores r ON r.transaction_id = t.id
 WHERE r.risk_level = 'high'
 GROUP BY t.merchant
 ORDER BY high_risk_txns DESC, total_amount DESC
 LIMIT 10;

-- 3c. Risk by time of day. Our model has no time-of-day feature, so if fraud
--     clusters at night here, that's a feature worth adding later.
SELECT CASE
         WHEN extract(hour FROM t.trans_time) < 6  THEN '1 late night (0-6)'
         WHEN extract(hour FROM t.trans_time) < 12 THEN '2 morning (6-12)'
         WHEN extract(hour FROM t.trans_time) < 18 THEN '3 afternoon (12-18)'
         ELSE                                           '4 evening (18-24)'
       END                                           AS time_of_day,
       count(*)                                      AS txns,
       count(*) FILTER (WHERE r.risk_level = 'high') AS high_risk,
       sum(t.is_fraud::int)                          AS actual_fraud
  FROM transactions t
  JOIN risk_scores r ON r.transaction_id = t.id
 GROUP BY 1
 ORDER BY 1;


-- ============================================================
-- 4. Looking inside the scores
-- ============================================================

-- 4a. One card's timeline around its first high-risk transaction (2 days either side).
--     Shows a fraud burst as it happened.
WITH first_high AS (
    SELECT t.cc_num, t.trans_time
      FROM transactions t
      JOIN risk_scores r ON r.transaction_id = t.id
     WHERE r.risk_level = 'high'
     ORDER BY t.trans_time
     LIMIT 1
)
SELECT t.trans_time,
       t.merchant,
       t.amount,
       r.risk_level,
       round(r.risk_score::numeric, 2) AS score,
       t.is_fraud
  FROM transactions t
  JOIN risk_scores r ON r.transaction_id = t.id
  JOIN first_high f  ON f.cc_num = t.cc_num
 WHERE t.trans_time BETWEEN f.trans_time - INTERVAL '2 days' AND f.trans_time + INTERVAL '2 days'
 ORDER BY t.trans_time;

-- 4b. Velocity bursts: transactions with 2+ others on the same card in the past hour.
--     features is JSONB; ->> pulls a field out as text, ::int converts it.
SELECT right(t.cc_num, 4)                        AS card,
       t.trans_time,
       t.amount,
       (r.features ->> 'txns_last_hour')::int    AS txns_last_hour,
       r.risk_level,
       t.is_fraud
  FROM transactions t
  JOIN risk_scores r ON r.transaction_id = t.id
 WHERE (r.features ->> 'txns_last_hour')::int >= 2
 ORDER BY txns_last_hour DESC, t.trans_time
 LIMIT 15;

-- 4c. The reasons the model gives most often for high-risk transactions.
--     jsonb_array_elements_text turns the reasons list into one row per reason;
--     regexp_replace hides the specific numbers and merchant names so similar
--     reasons group together.
SELECT regexp_replace(
           regexp_replace(reason, '(First time this card has paid).*', '\1 <merchant>'),
           '[0-9$.,]+', '#', 'g')                   AS reason_pattern,
       count(*)                                     AS times_given
  FROM risk_scores r,
       jsonb_array_elements_text(r.reasons) AS reason
 WHERE r.risk_level = 'high'
 GROUP BY 1
 ORDER BY times_given DESC;


-- ============================================================
-- 5. Vector search (pgvector)
--    <=> is cosine distance: 0 = same meaning, bigger = less similar.
-- ============================================================

-- 5a. The 5 transactions most similar in meaning to the first high-risk fraud.
--     (The first row is the transaction itself, at distance 0.)
SELECT round((r.embedding <=> (
           SELECT r2.embedding
             FROM risk_scores r2
             JOIN transactions t2 ON t2.id = r2.transaction_id
            WHERE t2.is_fraud AND r2.risk_level = 'high'
            ORDER BY r2.id
            LIMIT 1))::numeric, 3)  AS distance,
       left(r.summary, 120)         AS summary
  FROM risk_scores r
 ORDER BY r.embedding <=> (
           SELECT r2.embedding
             FROM risk_scores r2
             JOIN transactions t2 ON t2.id = r2.transaction_id
            WHERE t2.is_fraud AND r2.risk_level = 'high'
            ORDER BY r2.id
            LIMIT 1)
 LIMIT 5;

-- 5b. Hybrid search: same idea, but SQL filters first (high risk only, different
--     merchant), then vector similarity ranks what's left. This is what fixes the
--     "same merchant name dominates" problem we saw in 5a.
WITH q AS (
    SELECT r.embedding, t.merchant
      FROM risk_scores r
      JOIN transactions t ON t.id = r.transaction_id
     WHERE t.is_fraud AND r.risk_level = 'high'
     ORDER BY r.id
     LIMIT 1
)
SELECT round((r.embedding <=> q.embedding)::numeric, 3) AS distance,
       left(r.summary, 120)                            AS summary
  FROM risk_scores r
  JOIN transactions t ON t.id = r.transaction_id
 CROSS JOIN q
 WHERE r.risk_level = 'high'
   AND t.merchant <> q.merchant
 ORDER BY r.embedding <=> q.embedding
 LIMIT 5;


-- ============================================================
-- 6. Is the index being used? (EXPLAIN shows Postgres's plan)
-- ============================================================

-- 6a. Normal plan. On a small table Postgres may choose "Seq Scan" (read every row)
--     because that's cheaper than using the index.
EXPLAIN ANALYZE
SELECT r.id
  FROM risk_scores r
 ORDER BY r.embedding <=> (SELECT embedding FROM risk_scores ORDER BY id LIMIT 1)
 LIMIT 5;

-- 6b. Learning only: forbid sequential scans for one transaction to see the HNSW
--     index plan ("Index Scan using idx_risk_scores_embedding"). Never do this in app code.
BEGIN;
SET LOCAL enable_seqscan = off;
EXPLAIN ANALYZE
SELECT r.id
  FROM risk_scores r
 ORDER BY r.embedding <=> (SELECT embedding FROM risk_scores ORDER BY id LIMIT 1)
 LIMIT 5;
ROLLBACK;

-- 6c. Card-history lookup used on every insert: should use idx_transactions_card_time.
EXPLAIN ANALYZE
SELECT *
  FROM transactions
 WHERE cc_num = (SELECT cc_num FROM transactions ORDER BY id LIMIT 1)
   AND trans_time > TIMESTAMP '2020-07-01' - INTERVAL '1 hour';
