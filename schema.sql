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
