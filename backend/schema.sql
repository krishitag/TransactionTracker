-- Postgres schema for the Transaction Risk Platform.
-- Runs automatically the first time the Docker database starts (see docker-compose.yml).
-- Existing databases get later changes from backend/migrations/ instead.

-- pgvector: adds the vector column type and similarity search.
CREATE EXTENSION IF NOT EXISTS vector;

-- Raw transactions: facts that never change once recorded.
CREATE TABLE IF NOT EXISTS transactions (
    id          BIGSERIAL PRIMARY KEY,
    trans_num   TEXT UNIQUE NOT NULL,             -- external transaction ID
    cc_num      TEXT NOT NULL,                    -- card number; text, never used for maths
    merchant    TEXT NOT NULL,
    category    TEXT NOT NULL,
    amount      NUMERIC(12, 2) NOT NULL CHECK (amount >= 0),
    trans_time  TIMESTAMP NOT NULL,
    cust_lat    DOUBLE PRECISION NOT NULL,
    cust_long   DOUBLE PRECISION NOT NULL,
    merch_lat   DOUBLE PRECISION NOT NULL,
    merch_long  DOUBLE PRECISION NOT NULL,
    is_fraud    BOOLEAN,                          -- known label, if any; NULL for live traffic
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Scoring looks up "this card's recent transactions" on every insert.
CREATE INDEX IF NOT EXISTS idx_transactions_card_time ON transactions (cc_num, trans_time);

-- Model output: opinions about a transaction, which can change when the model is retrained.
CREATE TABLE IF NOT EXISTS risk_scores (
    id              BIGSERIAL PRIMARY KEY,
    transaction_id  BIGINT NOT NULL UNIQUE REFERENCES transactions (id) ON DELETE CASCADE,
    risk_score      DOUBLE PRECISION NOT NULL CHECK (risk_score BETWEEN 0 AND 1),
    risk_level      TEXT NOT NULL CHECK (risk_level IN ('low', 'medium', 'high')),
    reasons         JSONB NOT NULL,               -- plain-English reasons, most important first
    contributions   JSONB NOT NULL,               -- per-feature coefficient x scaled value
    features        JSONB NOT NULL,               -- feature values the model saw
    model_version   TEXT NOT NULL,
    scored_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    summary         TEXT,                         -- one-sentence description used for search
    embedding       vector(384)                   -- all-MiniLM-L6-v2 embedding of summary
);

-- Dashboard filters and counts by risk level.
CREATE INDEX IF NOT EXISTS idx_risk_scores_level ON risk_scores (risk_level);

-- Approximate nearest-neighbour search on embeddings, by cosine distance.
CREATE INDEX IF NOT EXISTS idx_risk_scores_embedding
    ON risk_scores USING hnsw (embedding vector_cosine_ops);
