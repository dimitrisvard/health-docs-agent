CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
  id          BIGSERIAL PRIMARY KEY,
  kind        TEXT NOT NULL,                 -- 'trial' | 'drug_label' | 'guideline'
  title       TEXT NOT NULL,
  source_uri  TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chunks (
  id           BIGSERIAL PRIMARY KEY,
  document_id  BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  section      TEXT,
  ordinal      INT NOT NULL,
  text         TEXT NOT NULL,
  token_count  INT,
  embedding    VECTOR(768),
  ts           TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', text)) STORED,
  metadata     JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS chunks_embedding_idx ON chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS chunks_ts_idx        ON chunks USING gin (ts);

CREATE TABLE IF NOT EXISTS messages (
  id          BIGSERIAL PRIMARY KEY,
  session_id  TEXT,
  role        TEXT NOT NULL,
  content     TEXT,
  tool_calls  JSONB,
  sources     JSONB,
  trace_id    TEXT,
  tokens_in   INT,
  tokens_out  INT,
  latency_ms  INT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS eval_runs (
  id          BIGSERIAL PRIMARY KEY,
  commit_sha  TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS eval_results (
  id           BIGSERIAL PRIMARY KEY,
  run_id       BIGINT NOT NULL REFERENCES eval_runs(id) ON DELETE CASCADE,
  question     TEXT NOT NULL,
  hit_at_k     BOOLEAN,
  mrr          REAL,
  ndcg         REAL,
  faithfulness REAL,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
