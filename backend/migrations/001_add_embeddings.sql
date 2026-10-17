-- Adds pgvector search to a database created before embeddings existed.
-- Safe to run more than once. Fresh databases already get this from schema.sql.

CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE risk_scores ADD COLUMN IF NOT EXISTS summary TEXT;
ALTER TABLE risk_scores ADD COLUMN IF NOT EXISTS embedding vector(384);

CREATE INDEX IF NOT EXISTS idx_risk_scores_embedding
    ON risk_scores USING hnsw (embedding vector_cosine_ops);
