// Server-only Google Business Profile integration for Cloudflare Pages.
// No credentials, resource IDs, or upstream error bodies are returned publicly.
const CANONICAL_ORIGIN = 'https://cascadepaintingpa.com';
const CALLBACK_PATH = '/api/google/callback';
const SCOPE = 'https://www.googleapis.com/auth/business.manage';
const TOKEN_URL = 'https://oauth2.googleapis.com/token';
const SIX_HOURS = 6 * 60 * 60 * 1000;
const RETENTION_MS = 29 * 24 * 60 * 60 * 1000;
const RETENTION_SECONDS = RETENTION_MS / 1000;
const BACKOFF_MS = 15 * 60 * 1000;
const STATE_MS = 10 * 60 * 1000;
const COOKIE_NAME = 'google_oauth_browser';
const encoder = new TextEncoder();
const decoder = new TextDecoder();

class IntegrationError extends Error {
  constructor(code, status = 503) { super(code); this.code = code; this.status = status; }
}

const secureHeaders = {
  'Cache-Control': 'no-store, max-age=0',
  Pragma: 'no-cache',
  'Referrer-Policy': 'no-referrer',
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
 'Content-Security-Policy': "default-src 'none'; form-action 'self' https://accounts.google.com; frame-ancestors 'none'; base-uri 'none'",
};

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
}

function html(title, body, status = 200, extraHeaders = {}) {
  return new Response(`<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escapeHtml(title)} | Cascade Painting</title></head><body><main><h1>${escapeHtml(title)}</h1>${body}<p><a href="/">Back to Cascade Painting</a></p></main></body></html>`, {
    status, headers: { ...secureHeaders, 'Content-Type': 'text/html; charset=utf-8', ...extraHeaders },
  });
}

function json(payload, status = 200) {
  return new Response(JSON.stringify(payload), { status, headers: { ...secureHeaders, 'Content-Type': 'application/json; charset=utf-8' } });
}

function methodNotAllowed(allow) {
  return new Response('Method not allowed', { status: 405, headers: { ...secureHeaders, Allow: allow } });
}

function toBase64(bytes) { return btoa(String.fromCharCode(...bytes)); }
function fromBase64(text) {
  try { return Uint8Array.from(atob(text), char => char.charCodeAt(0)); }
  catch { throw new IntegrationError('configuration'); }
}
function base64url(bytes) { return toBase64(bytes).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''); }
function randomSecret() { return base64url(crypto.getRandomValues(new Uint8Array(32))); }
async function sha256(value) { return base64url(new Uint8Array(await crypto.subtle.digest('SHA-256', encoder.encode(value)))); }
async function equalSecrets(first, second) {
  const [a, b] = await Promise.all([sha256(first), sha256(second)]);
  let difference = 0;
  for (let i = 0; i < a.length; i++) difference |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return difference === 0;
}

export function normalizeBusinessName(name) {
  return String(name || '').normalize('NFKC').trim().replace(/\s+/g, ' ').toLocaleLowerCase('en-US');
}

export function validateConfiguration(env, request) {
  if (!env.DB?.prepare || !env.GOOGLE_REVIEWS_CACHE?.get || !env.GOOGLE_REVIEWS_CACHE?.put || !env.GOOGLE_REVIEWS_CACHE?.delete ||
      !env.GOOGLE_CLIENT_ID || !env.GOOGLE_CLIENT_SECRET || !env.GOOGLE_REDIRECT_URI ||
      typeof env.GOOGLE_SETUP_PASSWORD !== 'string' || env.GOOGLE_SETUP_PASSWORD.length < 32 ||
      typeof env.GOOGLE_TOKEN_ENCRYPTION_KEY !== 'string') throw new IntegrationError('configuration');
  const keyBytes = fromBase64(env.GOOGLE_TOKEN_ENCRYPTION_KEY.trim());
  if (keyBytes.length !== 32) throw new IntegrationError('configuration');
  let redirect;
  try { redirect = new URL(env.GOOGLE_REDIRECT_URI); } catch { throw new IntegrationError('configuration'); }
  const local = ['localhost', '127.0.0.1', '[::1]'].includes(redirect.hostname);
  if (redirect.pathname !== CALLBACK_PATH || redirect.search || redirect.hash || redirect.username || redirect.password ||
      (!local && redirect.origin !== CANONICAL_ORIGIN) || (local && !['http:', 'https:'].includes(redirect.protocol))) {
    throw new IntegrationError('configuration');
  }
  if (request && new URL(request.url).origin !== redirect.origin) throw new IntegrationError('origin', 403);
  const parseID = (value, prefix) => {
    if (!value) return '';
    const id = String(value).replace(new RegExp(`^${prefix}/`), '');
    if (!/^[A-Za-z0-9_-]{1,128}$/.test(id)) throw new IntegrationError('configuration');
    return id;
  };
  return {
    env, keyBytes, redirect, local,
    businessName: String(env.GOOGLE_BUSINESS_NAME || 'Cascade Painting').trim(),
    accountID: parseID(env.GOOGLE_ACCOUNT_ID, 'accounts'),
    locationID: parseID(env.GOOGLE_LOCATION_ID, 'locations'),
  };
}

async function encryptionKey(config) { return crypto.subtle.importKey('raw', config.keyBytes, 'AES-GCM', false, ['encrypt', 'decrypt']); }

export async function encryptSecret(config, data, purpose) {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const bytes = await crypto.subtle.encrypt({ name: 'AES-GCM', iv, additionalData: encoder.encode(purpose) }, await encryptionKey(config), encoder.encode(JSON.stringify(data)));
  return `v1.${toBase64(iv)}.${toBase64(new Uint8Array(bytes))}`;
}

export async function decryptSecret(config, ciphertext, purpose) {
  try {
    const [version, iv, data, extra] = String(ciphertext).split('.');
    if (version !== 'v1' || !iv || !data || extra) throw new Error();
    const bytes = await crypto.subtle.decrypt({ name: 'AES-GCM', iv: fromBase64(iv), additionalData: encoder.encode(purpose) }, await encryptionKey(config), fromBase64(data));
    return JSON.parse(decoder.decode(bytes));
  } catch { throw new IntegrationError('encrypted_data'); }
}

function cookie(config, value, maxAge = STATE_MS / 1000) {
  // Browsers allow Secure cookies on localhost; HTTP local previews may not.
  const secure = config.redirect.protocol === 'https:' ? '; Secure' : '';
  return `${COOKIE_NAME}=${value}; Max-Age=${maxAge}; Path=/api/google; HttpOnly; SameSite=Lax${secure}`;
}

function readCookie(request) {
  const matches = (request.headers.get('Cookie') || '').split(';').map(s => s.trim()).filter(s => s.startsWith(`${COOKIE_NAME}=`));
  return matches.length === 1 ? matches[0].slice(COOKIE_NAME.length + 1) : '';
}

function ownerForm(action, label) {
  return html(label, `<p>Owner access is required to manage the Google Business Profile connection.</p><form method="post" action="${action}"><p><label for="password">Setup password</label><br><input id="password" name="password" type="password" autocomplete="current-password" maxlength="1024" required></p><button type="submit">${escapeHtml(label)}</button></form>`);
}

async function authenticateOwner(config, request) {
  const origin = request.headers.get('Origin');
  const fetchSite = request.headers.get('Sec-Fetch-Site');

  if (fetchSite && fetchSite !== 'same-origin') {
    throw new IntegrationError('origin', 403);
  }

  if (!fetchSite && origin && origin !== config.redirect.origin) {
    throw new IntegrationError('origin', 403);
  }

  if (
    !request.headers
      .get('Content-Type')
      ?.startsWith('application/x-www-form-urlencoded')
  ) {
    throw new IntegrationError('request', 400);
  }

  const body = await request.text();

  if (body.length > 4096) {
    throw new IntegrationError('request', 413);
  }

  const form = new URLSearchParams(body);

  if (form.getAll('password').length !== 1) {
    throw new IntegrationError('authorization', 403);
  }

  const now = Date.now();

  const visitorHash = await sha256(
    `setup:${request.headers.get('CF-Connecting-IP') || 'local'}:${config.env.GOOGLE_SETUP_PASSWORD}`
  );

  const db = config.env.DB;

  await db
    .prepare('DELETE FROM google_setup_attempts WHERE created_at < ?')
    .bind(now - BACKOFF_MS)
    .run();

  // One statement ensures simultaneous requests cannot bypass the attempt cap.
  const result = await db
    .prepare(
      'INSERT INTO google_setup_attempts(visitor_hash, created_at) SELECT ?, ? WHERE (SELECT COUNT(*) FROM google_setup_attempts WHERE visitor_hash = ? AND created_at >= ?) < 8 RETURNING created_at'
    )
    .bind(visitorHash, now, visitorHash, now - BACKOFF_MS)
    .first();

  if (!result) {
    throw new IntegrationError('rate_limit', 429);
  }

  if (
    !(await equalSecrets(
      form.get('password') || '',
      config.env.GOOGLE_SETUP_PASSWORD
    ))
  ) {
    throw new IntegrationError('authorization', 403);
  }
}

function ownerError(error, clearCookie) {
  const messages = {
    configuration: 'Google reviews setup is not configured yet. Check the server environment and database migration.',
    origin: 'Open this page on the configured website address to continue.',
    authorization: 'The setup password was not accepted.',
    rate_limit: 'Too many setup attempts. Please try again in 15 minutes.',
    state: 'This connection attempt expired or was already used. Start a new connection from this browser.',
    denied: 'Google authorization was not completed. Start a new connection when ready.',
    ambiguous_location: 'More than one matching business location was found. Set GOOGLE_ACCOUNT_ID and GOOGLE_LOCATION_ID, then connect again.',
    location_not_found: 'No matching business location was found. Check the business name and any configured account or location IDs, then connect again.',
    reconnect_required: 'Google authorization has expired or was revoked. Start a new connection.',
    google_access: 'Google denied API access. Check API approval, enabled APIs, permissions, and whether the business location is verified.',
    no_refresh_token: 'Google did not provide offline access. Remove this app from your Google account permissions, then connect again.',
  };
  return html('Google connection needs attention', `<p>${escapeHtml(messages[error?.code] || 'The Google connection could not be completed. Please try again or check the server configuration.')}</p><p><a href="/api/google/start">Start Google connection</a> · <a href="/api/google/status">Connection status</a></p>`, error?.status || 503, clearCookie ? { 'Set-Cookie': clearCookie } : {});
}

export async function handleGoogleStart({ request, env }) {
  if (!['GET', 'POST'].includes(request.method)) return methodNotAllowed('GET, POST');
  try {
    const config = validateConfiguration(env, request);
    if (new URL(request.url).search) throw new IntegrationError('request', 400);
    if (request.method === 'GET') return ownerForm('/api/google/start', 'Connect Google Business Profile');
    await authenticateOwner(config, request);
    const now = Date.now();
    const state = randomSecret();
    const browser = randomSecret();
    const verifier = randomSecret();
    await env.DB.prepare('DELETE FROM google_oauth_states WHERE expires_at <= ?').bind(now).run();
    await env.DB.prepare('INSERT INTO google_oauth_states(state_hash, browser_hash, pkce_ciphertext, expires_at) VALUES (?, ?, ?, ?)')
      .bind(await sha256(state), await sha256(browser), await encryptSecret(config, verifier, 'oauth-pkce'), now + STATE_MS).run();
    const authorize = new URL('https://accounts.google.com/o/oauth2/v2/auth');
    authorize.search = new URLSearchParams({
      client_id: env.GOOGLE_CLIENT_ID, redirect_uri: config.redirect.href, response_type: 'code', scope: SCOPE,
      access_type: 'offline', prompt: 'consent', state, code_challenge: await sha256(verifier), code_challenge_method: 'S256',
    }).toString();
    return new Response(null, { status: 303, headers: { ...secureHeaders, Location: authorize.href, 'Set-Cookie': cookie(config, browser) } });
  } catch (error) { return ownerError(error); }
}

async function fetchJSON(url, init = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 12000);
  try {
    const response = await fetch(url, { ...init, signal: controller.signal, redirect: 'error' });
    let data;
    try { data = await response.json(); } catch { throw new IntegrationError('google_response'); }
    if (!response.ok) {
      if (data?.error === 'invalid_grant') throw new IntegrationError('reconnect_required', 401);
      if (response.status === 401) throw new IntegrationError('google_unauthorized', 401);
      if (response.status === 403) throw new IntegrationError('google_access', 403);
      if (response.status === 429) throw new IntegrationError('google_rate_limit');
      throw new IntegrationError('google_unavailable');
    }
    if (!data || typeof data !== 'object' || Array.isArray(data)) throw new IntegrationError('google_response');
    return data;
  } catch (error) {
    if (error instanceof IntegrationError) throw error;
    throw new IntegrationError('google_unavailable');
  } finally { clearTimeout(timeout); }
}

async function exchangeToken(config, parameters) {
  return fetchJSON(TOKEN_URL, {
    method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ client_id: config.env.GOOGLE_CLIENT_ID, client_secret: config.env.GOOGLE_CLIENT_SECRET, ...parameters }),
  });
}

function parseTokenResponse(data, previousRefreshToken) {
  if (typeof data.access_token !== 'string' || !data.access_token || !Number.isFinite(Number(data.expires_in)) || Number(data.expires_in) <= 0) throw new IntegrationError('google_response');
  const refreshToken = data.refresh_token || previousRefreshToken;
  if (typeof refreshToken !== 'string' || !refreshToken) throw new IntegrationError('no_refresh_token');
  return { accessToken: data.access_token, refreshToken, expiresAt: Date.now() + Number(data.expires_in) * 1000 };
}

function bearer(accessToken) { return { headers: { Authorization: `Bearer ${accessToken}` } }; }

function safeGoogleMapsURL(value) {
  try {
    const url = new URL(value);
    if (url.protocol === 'https:' && ['google.com', 'www.google.com', 'maps.google.com', 'maps.app.goo.gl'].includes(url.hostname) && !url.username && !url.password) return url.href;
  } catch { /* Missing optional Google link. */ }
  return '';
}

async function discoverBusiness(config, accessToken) {
  const accounts = [];
  let token = '';
  const seenAccountPages = new Set();
  do {
    if (seenAccountPages.has(token) || seenAccountPages.size >= 100) throw new IntegrationError('google_response');
    seenAccountPages.add(token);
    const url = new URL('https://mybusinessaccountmanagement.googleapis.com/v1/accounts');
    url.search = new URLSearchParams({ pageSize: '20', ...(token ? { pageToken: token } : {}) });
    const data = await fetchJSON(url, bearer(accessToken));
    if (data.accounts && !Array.isArray(data.accounts)) throw new IntegrationError('google_response');
    accounts.push(...(data.accounts || []));
    token = data.nextPageToken || '';
  } while (token);
  const matches = [];
  for (const account of accounts) {
    const match = /^accounts\/([A-Za-z0-9_-]+)$/.exec(account.name || '');
    if (!match || (config.accountID && match[1] !== config.accountID)) continue;
    const accountID = match[1];
    token = '';
    const seenLocationPages = new Set();
    do {
      if (seenLocationPages.has(token) || seenLocationPages.size >= 100) throw new IntegrationError('google_response');
      seenLocationPages.add(token);
      const url = new URL(`https://mybusinessbusinessinformation.googleapis.com/v1/accounts/${accountID}/locations`);
      url.search = new URLSearchParams({ readMask: 'name,title,metadata', pageSize: '100', ...(token ? { pageToken: token } : {}) });
      const data = await fetchJSON(url, bearer(accessToken));
      if (data.locations && !Array.isArray(data.locations)) throw new IntegrationError('google_response');
      for (const location of data.locations || []) {
        const resource = /^locations\/([A-Za-z0-9_-]+)$/.exec(location.name || '');
        if (!resource || normalizeBusinessName(location.title) !== normalizeBusinessName(config.businessName) || (config.locationID && resource[1] !== config.locationID)) continue;
        if (!matches.some(existing => existing.accountID === accountID && existing.locationID === resource[1])) {
          matches.push({ accountID, locationID: resource[1], businessName: location.title, mapsURL: safeGoogleMapsURL(location.metadata?.mapsUri) });
        }
      }
      token = data.nextPageToken || '';
    } while (token);
  }
  if (!matches.length) throw new IntegrationError('location_not_found', 400);
  if (matches.length !== 1) throw new IntegrationError('ambiguous_location', 409);
  return matches[0];
}

export async function handleGoogleCallback({ request, env }) {
  if (request.method !== 'GET') return methodNotAllowed('GET');
  let config;
  try {
    config = validateConfiguration(env, request);
    const params = new URL(request.url).searchParams;
    const state = params.get('state') || '';
    const browser = readCookie(request);
    if (params.getAll('state').length !== 1 || !/^[A-Za-z0-9_-]{43}$/.test(state) || !/^[A-Za-z0-9_-]{43}$/.test(browser)) throw new IntegrationError('state', 400);
    // DELETE ... RETURNING atomically consumes the state, including denied grants.
    const stored = await env.DB.prepare('DELETE FROM google_oauth_states WHERE state_hash = ? AND browser_hash = ? AND expires_at > ? RETURNING pkce_ciphertext')
      .bind(await sha256(state), await sha256(browser), Date.now()).first();
    if (!stored) throw new IntegrationError('state', 400);
    if (params.has('error')) throw new IntegrationError('denied', 400);
    const code = params.get('code');
    if (params.getAll('code').length !== 1 || !code || code.length > 8192) throw new IntegrationError('state', 400);
    const verifier = await decryptSecret(config, stored.pkce_ciphertext, 'oauth-pkce');
    const data = await exchangeToken(config, { grant_type: 'authorization_code', code, redirect_uri: config.redirect.href, code_verifier: verifier });
    // A reconnect can omit refresh_token; keep the existing grant only when the
    // discovered account/location pair below is exactly the same as before.
    const business = await discoverBusiness(config, data.access_token);
    const previous = await env.DB.prepare('SELECT * FROM google_business_connection WHERE id = 1').first();
    let previousRefresh;
    if (!data.refresh_token && previous && previous.account_id === business.accountID && previous.location_id === business.locationID) {
      previousRefresh = (await decryptSecret(config, previous.tokens_ciphertext, 'google-tokens')).refreshToken;
    }
    const tokens = parseTokenResponse(data, previousRefresh);
    const encryptedTokens = await encryptSecret(config, tokens, 'google-tokens');
    const oldCache = await env.DB.prepare('SELECT payload_key FROM google_reviews_cache WHERE id = 1').first();
    const now = Date.now();
    await env.DB.batch([
      env.DB.prepare(`INSERT INTO google_business_connection(id, tokens_ciphertext, account_id, location_id, business_name, maps_url, connected_at, updated_at, auth_status, last_error_code)
        VALUES (1, ?, ?, ?, ?, ?, ?, ?, 'connected', NULL)
        ON CONFLICT(id) DO UPDATE SET tokens_ciphertext=excluded.tokens_ciphertext, account_id=excluded.account_id, location_id=excluded.location_id,
        business_name=excluded.business_name, maps_url=excluded.maps_url, connected_at=excluded.connected_at, updated_at=excluded.updated_at, auth_status='connected', last_error_code=NULL`)
        .bind(encryptedTokens, business.accountID, business.locationID, business.businessName, business.mapsURL, now, now),
      env.DB.prepare('UPDATE google_reviews_cache SET payload_key=NULL, fetched_at=NULL, retry_after=0, lock_token=NULL, lock_until=0, last_error_code=NULL WHERE id=1'),
    ]);
    if (oldCache?.payload_key) await env.GOOGLE_REVIEWS_CACHE.delete(oldCache.payload_key);
    return html('Google Business Profile connected', '<p>Your business location is connected. Reviews will load on the website when the reviews section is visited.</p><p><a href="/api/google/status">Check connection status</a> · <a href="/reviews/">View reviews page</a></p>', 200, { 'Set-Cookie': cookie(config, '', 0) });
  } catch (error) { return ownerError(error, config ? cookie(config, '', 0) : undefined); }
}

function safeDate(value) {
  const ms = typeof value === 'string' ? Date.parse(value) : NaN;
  return Number.isFinite(ms) ? new Date(ms).toISOString() : null;
}

function safePhotoURL(value) {
  try { const url = new URL(value); return url.protocol === 'https:' && !url.username && !url.password ? url.href : ''; }
  catch { return ''; }
}

export function normalizeReviews(data) {
  if (!data || typeof data !== 'object' || (data.reviews != null && !Array.isArray(data.reviews))) throw new IntegrationError('google_response');
  const count = Number(data.totalReviewCount ?? 0);
  const rating = data.averageRating == null ? null : Number(data.averageRating);
  if (!Number.isInteger(count) || count < 0 || (rating !== null && (!Number.isFinite(rating) || rating < 0 || rating > 5))) throw new IntegrationError('google_response');
  const stars = { ONE: 1, TWO: 2, THREE: 3, FOUR: 4, FIVE: 5 };
  const reviews = (data.reviews || []).slice(0, 50).map(review => {
    if (!stars[review.starRating]) throw new IntegrationError('google_response');
    return {
      reviewer: { displayName: typeof review.reviewer?.displayName === 'string' && review.reviewer.displayName.trim() ? review.reviewer.displayName : 'Google user', profilePhotoUrl: safePhotoURL(review.reviewer?.profilePhotoUrl) },
      starRating: stars[review.starRating], comment: typeof review.comment === 'string' ? review.comment : '',
      createTime: safeDate(review.createTime), updateTime: safeDate(review.updateTime),
    };
  });
  return { reviews, averageRating: count ? rating : null, totalReviewCount: count };
}

function emptyPayload() {
  return { status: 'unavailable', reviews: [], averageRating: null, totalReviewCount: 0, updatedAt: null, googleMapsUrl: '' };
}

async function readCache(config) {
  const meta = await config.env.DB.prepare('SELECT * FROM google_reviews_cache WHERE id=1').first();
  if (!meta?.payload_key) return { meta, payload: null };
  if (!meta.fetched_at || Date.now() - meta.fetched_at >= RETENTION_MS) {
    await config.env.GOOGLE_REVIEWS_CACHE.delete(meta.payload_key);
    await config.env.DB.prepare('UPDATE google_reviews_cache SET payload_key=NULL, fetched_at=NULL WHERE id=1 AND payload_key=?').bind(meta.payload_key).run();
    return { meta: { ...meta, payload_key: null, fetched_at: null }, payload: null };
  }
  try {
    const encrypted = await config.env.GOOGLE_REVIEWS_CACHE.get(meta.payload_key);
    if (!encrypted) return { meta, payload: null };
    const payload = await decryptSecret(config, encrypted, 'google-reviews');
    if (!Array.isArray(payload.reviews) || typeof payload.totalReviewCount !== 'number' || payload.updatedAt !== new Date(meta.fetched_at).toISOString()) throw new IntegrationError('encrypted_data');
    return { meta, payload };
  } catch { return { meta, payload: null }; }
}

async function currentTokens(config, connection, forceRefresh = false) {
  let tokens = await decryptSecret(config, connection.tokens_ciphertext, 'google-tokens');
  if (!forceRefresh && tokens.accessToken && tokens.expiresAt > Date.now() + 60000) return tokens;
  if (!tokens.refreshToken) throw new IntegrationError('reconnect_required', 401);
  tokens = parseTokenResponse(await exchangeToken(config, { grant_type: 'refresh_token', refresh_token: tokens.refreshToken }), tokens.refreshToken);
  const ciphertext = await encryptSecret(config, tokens, 'google-tokens');
  const updated = await config.env.DB.prepare("UPDATE google_business_connection SET tokens_ciphertext=?, updated_at=?, auth_status='connected', last_error_code=NULL WHERE id=1 AND tokens_ciphertext=? RETURNING id")
    .bind(ciphertext, Date.now(), connection.tokens_ciphertext).first();
  if (!updated) throw new IntegrationError('connection_changed');
  connection.tokens_ciphertext = ciphertext;
  return tokens;
}

async function refreshReviews(config, connection, lockToken) {
  let newKey;
  try {
    let tokens = await currentTokens(config, connection);
    const url = `https://mybusiness.googleapis.com/v4/accounts/${encodeURIComponent(connection.account_id)}/locations/${encodeURIComponent(connection.location_id)}/reviews?pageSize=50&orderBy=updateTime%20desc`;
    let data;
    try { data = await fetchJSON(url, bearer(tokens.accessToken)); }
    catch (error) {
      if (error.code !== 'google_unauthorized') throw error;
      tokens = await currentTokens(config, connection, true);
      data = await fetchJSON(url, bearer(tokens.accessToken));
    }
    const fetchedAt = Date.now();
    const normalized = normalizeReviews(data);
    const payload = { status: normalized.totalReviewCount === 0 ? 'empty' : 'ok', ...normalized, updatedAt: new Date(fetchedAt).toISOString(), googleMapsUrl: safeGoogleMapsURL(connection.maps_url) };
    const previous = await config.env.DB.prepare('SELECT payload_key FROM google_reviews_cache WHERE id=1').first();
    newKey = `google-reviews:${randomSecret()}`;
    await config.env.GOOGLE_REVIEWS_CACHE.put(newKey, await encryptSecret(config, payload, 'google-reviews'), { expirationTtl: RETENTION_SECONDS });
    const saved = await config.env.DB.prepare('UPDATE google_reviews_cache SET payload_key=?, fetched_at=?, retry_after=0, lock_token=NULL, lock_until=0, last_error_code=NULL WHERE id=1 AND lock_token=? RETURNING id')
      .bind(newKey, fetchedAt, lockToken).first();
    if (!saved) {
      await config.env.GOOGLE_REVIEWS_CACHE.delete(newKey);
      return null;
    }
    if (previous?.payload_key) await config.env.GOOGLE_REVIEWS_CACHE.delete(previous.payload_key);
    return payload;
  } catch (error) {
    if (newKey) await config.env.GOOGLE_REVIEWS_CACHE.delete(newKey).catch(() => {});
    const reconnect = error.code === 'reconnect_required';
    const safeCode = error instanceof IntegrationError ? error.code : 'storage_unavailable';
    if (reconnect) {
      await config.env.DB.prepare("UPDATE google_business_connection SET auth_status='reconnect_required', last_error_code='reconnect_required', updated_at=? WHERE id=1 AND tokens_ciphertext=?")
        .bind(Date.now(), connection.tokens_ciphertext).run();
    }
    await config.env.DB.prepare('UPDATE google_reviews_cache SET retry_after=?, lock_token=NULL, lock_until=0, last_error_code=? WHERE id=1 AND lock_token=?')
      .bind(Date.now() + (reconnect ? SIX_HOURS : BACKOFF_MS), safeCode, lockToken).run();
    return null;
  }
}

export async function handleReviews({ request, env }) {
  if (request.method !== 'GET') return methodNotAllowed('GET');
  try {
    const config = validateConfiguration(env, request);
    const cached = await readCache(config);
    if (cached.payload && Date.now() - cached.meta.fetched_at < SIX_HOURS) return json(cached.payload);
    const stale = cached.payload ? { ...cached.payload, status: 'stale' } : emptyPayload();
    const connection = await env.DB.prepare('SELECT * FROM google_business_connection WHERE id=1').first();
    if (!connection || connection.auth_status !== 'connected' || cached.meta?.retry_after > Date.now()) return json(stale);
    const lockToken = randomSecret();
    const now = Date.now();
    // A single writer fetches Google; concurrent visitors receive cached content.
    const lease = await env.DB.prepare('UPDATE google_reviews_cache SET lock_token=?, lock_until=? WHERE id=1 AND lock_until <= ? AND retry_after <= ? RETURNING id')
      .bind(lockToken, now + 90000, now, now).first();
    if (!lease) return json(stale);
    const refreshed = await refreshReviews(config, connection, lockToken);
    return json(refreshed || stale);
  } catch { return json(emptyPayload()); }
}

export async function handleGoogleStatus({ request, env }) {
  if (!['GET', 'POST'].includes(request.method)) return methodNotAllowed('GET, POST');
  try {
    const config = validateConfiguration(env, request);
    if (new URL(request.url).search) throw new IntegrationError('request', 400);
    if (request.method === 'GET') return ownerForm('/api/google/status', 'Check Google connection');
    await authenticateOwner(config, request);
    const connection = await env.DB.prepare('SELECT * FROM google_business_connection WHERE id=1').first();
    const cached = await readCache(config);
    const authStatus = !connection ? 'Not connected' : connection.auth_status === 'reconnect_required' ? 'Reconnect required' : 'Connected';
    const cacheStatus = !cached.payload ? 'No cached reviews' : Date.now() - cached.meta.fetched_at < SIX_HOURS ? 'Current' : 'Stale; Google refresh pending';
    const labels = {
      google_access: 'Google API access denied: check approval, enabled APIs, business permissions, and location verification.',
      google_unauthorized: 'Google rejected the access token after retry; reconnect the account.',
      reconnect_required: 'Google authorization expired or was revoked; reconnect the account.',
      google_rate_limit: 'Google temporarily limited requests. The next attempt is delayed.',
      google_unavailable: 'Google could not be reached. The next attempt is delayed.',
      encrypted_data: 'Stored data could not be decrypted. Check the encryption key and reconnect if it changed.',
    };
    const error = cached.meta?.last_error_code;
    return html('Google connection status', `<dl><dt>Authorization</dt><dd>${authStatus}</dd><dt>Business</dt><dd>${escapeHtml(connection?.business_name || config.businessName)}</dd><dt>Review cache</dt><dd>${cacheStatus}</dd><dt>Google review count</dt><dd>${cached.payload ? cached.payload.totalReviewCount : 'Unavailable'}</dd><dt>Last successful refresh</dt><dd>${escapeHtml(cached.payload?.updatedAt || 'Not yet refreshed')}</dd></dl>${error ? `<p>${escapeHtml(labels[error] || 'The last refresh failed. Cached reviews remain available until their retention limit.')}</p>` : ''}<p><a href="/api/google/start">Connect or reconnect Google</a></p>`);
  } catch (error) { return ownerError(error); }
}
