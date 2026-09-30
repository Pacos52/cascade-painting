import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import {
  decryptSecret,
  encryptSecret,
  handleGoogleCallback,
  handleGoogleStart,
  handleReviews,
  normalizeBusinessName,
  normalizeReviews,
  validateConfiguration,
} from '../server/google-business.js';

const secretValue = 'private-value-that-must-never-be-returned';
const encryptionKey = Buffer.alloc(32, 7).toString('base64');

class Statement {
  constructor(db, sql) { this.db = db; this.sql = sql; this.values = []; }
  bind(...values) { this.values = values; return this; }
  async run() {
    if (this.sql.startsWith('INSERT INTO google_oauth_states')) this.db.oauthState = this.values;
    return { success: true };
  }
  async first() {
    if (this.sql.startsWith('INSERT INTO google_setup_attempts')) return { created_at: this.values[1] };
    if (this.sql.includes('SELECT * FROM google_reviews_cache')) return { id: 1, payload_key: null, fetched_at: null, retry_after: 0, lock_until: 0 };
    if (this.sql.includes('SELECT * FROM google_business_connection')) return null;
    return null;
  }
}

class FakeDB {
  prepare(sql) { return new Statement(this, sql); }
}

function environment() {
  return {
    DB: new FakeDB(),
    GOOGLE_REVIEWS_CACHE: { get: async () => null, put: async () => {}, delete: async () => {} },
    GOOGLE_CLIENT_ID: 'test-client.apps.googleusercontent.com',
    GOOGLE_CLIENT_SECRET: secretValue,
    GOOGLE_REDIRECT_URI: 'https://cascadepaintingpa.com/api/google/callback',
    GOOGLE_SETUP_PASSWORD: 'a-setup-password-that-is-at-least-32-characters',
    GOOGLE_TOKEN_ENCRYPTION_KEY: encryptionKey,
  };
}

test('normalizes business names and Google review fields', () => {
  assert.equal(normalizeBusinessName('  Cascade   Painting '), 'cascade painting');
  const result = normalizeReviews({
    averageRating: 4.8,
    totalReviewCount: 1,
    reviews: [{
      reviewer: { displayName: 'A Customer', profilePhotoUrl: 'https://lh3.googleusercontent.com/photo' },
      starRating: 'FIVE',
      comment: 'Careful work.',
      createTime: '2026-09-01T10:00:00Z',
      updateTime: '2026-09-01T10:00:00Z',
    }],
  });
  assert.equal(result.averageRating, 4.8);
  assert.equal(result.totalReviewCount, 1);
  assert.deepEqual(result.reviews[0].starRating, 5);
});

test('encrypts stored values with authenticated encryption', async () => {
  const env = environment();
  const config = validateConfiguration(env, new Request(env.GOOGLE_REDIRECT_URI));
  const ciphertext = await encryptSecret(config, { refreshToken: secretValue }, 'test-purpose');
  assert.ok(!ciphertext.includes(secretValue));
  assert.deepEqual(await decryptSecret(config, ciphertext, 'test-purpose'), { refreshToken: secretValue });
  await assert.rejects(() => decryptSecret(config, ciphertext, 'wrong-purpose'));
});

test('OAuth start requires owner password and produces an offline PKCE request', async () => {
  const env = environment();
  const request = new Request('https://cascadepaintingpa.com/api/google/start', {
    method: 'POST',
    headers: { Origin: 'https://cascadepaintingpa.com', 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ password: env.GOOGLE_SETUP_PASSWORD }),
  });
  const response = await handleGoogleStart({ request, env });
  assert.equal(response.status, 200);
  assert.match(response.headers.get('content-type'), /text\/html/);
  assert.equal(response.headers.get('location'), null);
  assert.match(response.headers.get('set-cookie'), /HttpOnly; SameSite=Lax; Secure/);

  const page = await response.text();
  const link = page.match(/<a href="([^"]+)">Continue with Google<\/a>/);
  assert.ok(link, 'password submission should render an explicit Google continuation link');
  const target = new URL(link[1].replaceAll('&amp;', '&'));
  assert.equal(target.origin, 'https://accounts.google.com');
  assert.equal(target.searchParams.get('access_type'), 'offline');
  assert.equal(target.searchParams.get('prompt'), 'consent');
  assert.equal(target.searchParams.get('code_challenge_method'), 'S256');
  assert.equal(target.searchParams.get('redirect_uri'), env.GOOGLE_REDIRECT_URI);
  assert.match(target.searchParams.get('state'), /^[A-Za-z0-9_-]{43}$/);
  assert.match(target.searchParams.get('code_challenge'), /^[A-Za-z0-9_-]{43}$/);
  assert.ok(env.DB.oauthState);
  assert.ok(!page.includes(secretValue));
  assert.ok(!target.href.includes(secretValue));
});

test('missing configuration fails safely and public reviews expose no secrets', async () => {
  const callback = await handleGoogleCallback({ request: new Request('https://cascadepaintingpa.com/api/google/callback'), env: {} });
  assert.equal(callback.status, 503);
  assert.ok(!(await callback.text()).includes(secretValue));

  const env = environment();
  const response = await handleReviews({ request: new Request('https://cascadepaintingpa.com/api/reviews'), env });
  assert.equal(response.status, 200);
  const text = await response.text();
  assert.ok(!text.includes(secretValue));
  assert.deepEqual(Object.keys(JSON.parse(text)).sort(), ['averageRating', 'googleMapsUrl', 'reviews', 'status', 'totalReviewCount', 'updatedAt'].sort());
});

test('generated pages and client script consume the same-origin reviews endpoint', async () => {
  const [home, reviews, script] = await Promise.all([
    readFile(new URL('../public/index.html', import.meta.url), 'utf8'),
    readFile(new URL('../public/reviews/index.html', import.meta.url), 'utf8'),
    readFile(new URL('../public/assets/google-reviews.js', import.meta.url), 'utf8'),
  ]);
  assert.match(home, /data-google-reviews/);
  assert.match(reviews, /data-review-limit="12"/);
  assert.match(script, /fetch\('\/api\/reviews'/);
  assert.doesNotMatch(script, /GOOGLE_CLIENT_SECRET|refreshToken/);
});
