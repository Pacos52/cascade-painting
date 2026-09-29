-- OAuth tokens are AES-GCM encrypted by the application before storage.
-- Google review content lives only in encrypted, automatically expiring KV.
CREATE TABLE IF NOT EXISTS google_oauth_states (
  state_hash TEXT PRIMARY KEY,
  browser_hash TEXT NOT NULL,
  pkce_ciphertext TEXT NOT NULL,
  expires_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_google_oauth_expiry ON google_oauth_states(expires_at);

CREATE TABLE IF NOT EXISTS google_business_connection (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  tokens_ciphertext TEXT NOT NULL,
  account_id TEXT NOT NULL,
  location_id TEXT NOT NULL,
  business_name TEXT NOT NULL,
  maps_url TEXT NOT NULL DEFAULT '',
  connected_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,
  auth_status TEXT NOT NULL DEFAULT 'connected',
  last_error_code TEXT
);

CREATE TABLE IF NOT EXISTS google_reviews_cache (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  payload_key TEXT,
  fetched_at INTEGER,
  retry_after INTEGER NOT NULL DEFAULT 0,
  lock_token TEXT,
  lock_until INTEGER NOT NULL DEFAULT 0,
  last_error_code TEXT
);
INSERT OR IGNORE INTO google_reviews_cache(id) VALUES (1);

CREATE TABLE IF NOT EXISTS google_setup_attempts (
  visitor_hash TEXT NOT NULL,
  created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_google_setup_attempts ON google_setup_attempts(visitor_hash, created_at);
