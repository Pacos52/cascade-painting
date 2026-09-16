const reply = (body, status = 200) => new Response(body ? JSON.stringify(body) : null, {
  status,
  headers: { 'content-type':'application/json; charset=utf-8', 'cache-control':'no-store', 'x-content-type-options':'nosniff' }
});
const clean = (value, max = 500) => String(value || '').trim().slice(0, max);
export async function onRequestPost({ request, env }) {
  const origin = request.headers.get('origin');
  const siteOrigin = new URL(request.url).origin;
  if (origin && origin !== siteOrigin) return reply({ ok:false }, 403);
  if (!(request.headers.get('content-type') || '').toLowerCase().includes('application/json')) return reply({ ok:false }, 415);
  let body;
  try { body = await request.json(); } catch { return reply({ ok:false }, 400); }
  const eventName = clean(body?.event, 80);
  const path = clean(body?.path, 500);
  if (!eventName || !path) return reply({ ok:false }, 400);
  if (!env.DB) return new Response(null, { status:204, headers:{'cache-control':'no-store'} });
  const allowed = new Set(['page_view','phone_click','email_click','google_profile_click','project_view_click','resource_click','estimate_cta_click','scroll_depth','estimate_step_continue','estimate_submit_attempt','lead_submit_success']);
  if (!allowed.has(eventName)) return reply({ ok:false }, 400);
  let detail = {};
  if (body.detail && typeof body.detail === 'object' && !Array.isArray(body.detail)) detail = body.detail;
  const detailJson = JSON.stringify(detail).slice(0, 3000);
  try {
    await env.DB.prepare('INSERT INTO web_events (id, created_at, session_id, event_name, path, referrer, detail_json) VALUES (?, ?, ?, ?, ?, ?, ?)')
      .bind(crypto.randomUUID(), new Date().toISOString(), clean(body.sessionId, 100), eventName, path, clean(body.referrer, 1000), detailJson).run();
  } catch (_) { return new Response(null, { status:204, headers:{'cache-control':'no-store'} }); }
  return new Response(null, { status:204, headers:{'cache-control':'no-store'} });
}
export function onRequestGet() { return reply({ ok:false, error:'method_not_allowed' }, 405); }
