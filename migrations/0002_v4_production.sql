-- Apply only to an existing V3 D1 database. Fresh databases should use schema.sql.
ALTER TABLE leads ADD COLUMN source_page TEXT;
ALTER TABLE leads ADD COLUMN landing_page TEXT;
ALTER TABLE leads ADD COLUMN referrer TEXT;
ALTER TABLE leads ADD COLUMN utm_source TEXT;
ALTER TABLE leads ADD COLUMN utm_medium TEXT;
ALTER TABLE leads ADD COLUMN utm_campaign TEXT;
ALTER TABLE leads ADD COLUMN utm_content TEXT;
ALTER TABLE leads ADD COLUMN utm_term TEXT;
ALTER TABLE leads ADD COLUMN gclid TEXT;
ALTER TABLE leads ADD COLUMN status TEXT NOT NULL DEFAULT 'new';
CREATE INDEX IF NOT EXISTS idx_leads_status_created ON leads(status, created_at DESC);
CREATE TABLE IF NOT EXISTS web_events (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, session_id TEXT, event_name TEXT NOT NULL, path TEXT NOT NULL, referrer TEXT, detail_json TEXT);
CREATE INDEX IF NOT EXISTS idx_web_events_created ON web_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_web_events_event_created ON web_events(event_name, created_at DESC);
CREATE TABLE IF NOT EXISTS lead_rate_limit (visitor_hash TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_lead_rate_limit_hash_created ON lead_rate_limit(visitor_hash, created_at DESC);
