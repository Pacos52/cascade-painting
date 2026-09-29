CREATE TABLE IF NOT EXISTS leads (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  name TEXT NOT NULL,
  phone TEXT NOT NULL,
  email TEXT NOT NULL,
  project_type TEXT NOT NULL,
  location TEXT NOT NULL,
  timing TEXT NOT NULL,
  details TEXT NOT NULL,
  source TEXT NOT NULL,
  source_page TEXT,
  landing_page TEXT,
  referrer TEXT,
  utm_source TEXT,
  utm_medium TEXT,
  utm_campaign TEXT,
  utm_content TEXT,
  utm_term TEXT,
  gclid TEXT,
  status TEXT NOT NULL DEFAULT 'new'
);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_leads_status_created ON leads(status, created_at DESC);

CREATE TABLE IF NOT EXISTS web_events (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  session_id TEXT,
  event_name TEXT NOT NULL,
  path TEXT NOT NULL,
  referrer TEXT,
  detail_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_web_events_created ON web_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_web_events_event_created ON web_events(event_name, created_at DESC);

CREATE TABLE IF NOT EXISTS lead_rate_limit (
  visitor_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_lead_rate_limit_hash_created ON lead_rate_limit(visitor_hash, created_at DESC);

-- Google OAuth tokens and PKCE verifiers are AES-GCM encrypted by the
-- application before storage. Review content lives in expiring encrypted KV.
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
