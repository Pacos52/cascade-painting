const json = (body, status = 200) => new Response(JSON.stringify(body), {
  status,
  headers: {
    'content-type': 'application/json; charset=utf-8',
    'cache-control': 'no-store',
    'x-content-type-options': 'nosniff'
  }
});

const clean = (value, max = 240) => String(value || '').trim().slice(0, max);

export async function onRequestPost(context) {
  const { request, env } = context;
  const origin = request.headers.get('origin');
  const siteOrigin = new URL(request.url).origin;
  if (origin && origin !== siteOrigin) return json({ ok: false, error: 'origin_not_allowed' }, 403);

  const contentType = request.headers.get('content-type') || '';
  if (!contentType.toLowerCase().includes('application/json')) {
    return json({ ok: false, error: 'unsupported_media_type' }, 415);
  }
  const declaredLength = Number(request.headers.get('content-length') || 0);
  if (declaredLength > 24000) return json({ ok: false, error: 'payload_too_large' }, 413);

  let body;
  try { body = await request.json(); }
  catch { return json({ ok: false, error: 'invalid_json' }, 400); }
  if (!body || typeof body !== 'object' || Array.isArray(body)) return json({ ok: false, error: 'invalid_body' }, 400);
  if (JSON.stringify(body).length > 24000) return json({ ok: false, error: 'payload_too_large' }, 413);

  if (body.website) return json({ ok: true }); // Honeypot: silently accept bots.

  // Optional rate limiting when D1 + RATE_LIMIT_SALT are configured. Raw IP addresses are never stored.
  if (env.DB && env.RATE_LIMIT_SALT) {
    try {
      const ip = request.headers.get('cf-connecting-ip') || '';
      if (ip) {
        const bytes = new TextEncoder().encode(`${env.RATE_LIMIT_SALT}:${ip}`);
        const digest = await crypto.subtle.digest('SHA-256', bytes);
        const visitorHash = [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2,'0')).join('');
        const cutoff = new Date(Date.now() - 15 * 60 * 1000).toISOString();
        const row = await env.DB.prepare('SELECT COUNT(*) AS count FROM lead_rate_limit WHERE visitor_hash = ? AND created_at >= ?').bind(visitorHash, cutoff).first();
        if (Number(row?.count || 0) >= 5) return json({ ok:false, error:'rate_limited' }, 429);
        await env.DB.prepare('INSERT INTO lead_rate_limit (visitor_hash, created_at) VALUES (?, ?)').bind(visitorHash, new Date().toISOString()).run();
      }
    } catch (_) { /* fail open if the optional rate-limit table has not been migrated yet */ }
  }

  const required = ['name', 'phone', 'email', 'projectType', 'location', 'timing', 'details'];
  for (const key of required) {
    if (!clean(body[key], 6000)) return json({ ok: false, error: `missing_${key}` }, 400);
  }

  const email = clean(body.email, 180).toLowerCase();
  const phone = clean(body.phone, 40);
  if (!/^\S+@\S+\.\S+$/.test(email)) return json({ ok: false, error: 'invalid_email' }, 400);
  if (phone.replace(/\D/g, '').length < 7) return json({ ok: false, error: 'invalid_phone' }, 400);
  if (clean(body.details, 6000).length > 5000) return json({ ok: false, error: 'details_too_long' }, 400);

  const contextData = {
    sourcePage: clean(body.sourcePage, 1000),
    landingPage: clean(body.landingPage, 1000),
    referrer: clean(body.referrer, 1000),
    utmSource: clean(body.utmSource, 180),
    utmMedium: clean(body.utmMedium, 180),
    utmCampaign: clean(body.utmCampaign, 240),
    utmContent: clean(body.utmContent, 240),
    utmTerm: clean(body.utmTerm, 240),
    gclid: clean(body.gclid, 300)
  };

  const lead = {
    id: crypto.randomUUID(),
    createdAt: new Date().toISOString(),
    name: clean(body.name, 140),
    phone,
    email,
    projectType: clean(body.projectType, 120),
    location: clean(body.location, 180),
    timing: clean(body.timing, 120),
    details: clean(body.details, 5000),
    source: 'cascadepaintingpa.com',
    context: contextData
  };

  const successes = [];
  const failures = [];

  // Optional D1 persistence. The core lead fields intentionally remain compatible with schema.sql.
  if (env.DB) {
    try {
      await env.DB.prepare(`INSERT INTO leads (id, created_at, name, phone, email, project_type, location, timing, details, source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`)
        .bind(lead.id, lead.createdAt, lead.name, lead.phone, lead.email, lead.projectType, lead.location, lead.timing, lead.details, lead.source).run();
      successes.push('database');
    } catch (_) { failures.push('database'); }
  }

  // Optional CRM/webhook handoff. Attribution travels with the lead for future reporting.
  if (env.CRM_WEBHOOK_URL) {
    try {
      const response = await fetch(env.CRM_WEBHOOK_URL, {
        method: 'POST',
        headers: {
          'content-type': 'application/json',
          ...(env.CRM_WEBHOOK_TOKEN ? { 'authorization': `Bearer ${env.CRM_WEBHOOK_TOKEN}` } : {})
        },
        body: JSON.stringify({ event: 'lead.created', lead })
      });
      if (!response.ok) throw new Error('webhook_failed');
      successes.push('crm');
    } catch (_) { failures.push('crm'); }
  }

  // Optional Resend email delivery.
  if (env.RESEND_API_KEY && env.LEAD_TO_EMAIL && env.LEAD_FROM_EMAIL) {
    try {
      const safe = value => String(value).replace(/[<>&]/g, char => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;' }[char]));
      const attributionRows = [
        ['Source page', lead.context.sourcePage],
        ['Landing page', lead.context.landingPage],
        ['Referrer', lead.context.referrer],
        ['UTM source', lead.context.utmSource],
        ['UTM medium', lead.context.utmMedium],
        ['UTM campaign', lead.context.utmCampaign],
        ['GCLID', lead.context.gclid]
      ].filter(([, value]) => value);
      const attributionHtml = attributionRows.length
        ? `<hr><h3>Attribution</h3>${attributionRows.map(([label, value]) => `<p><strong>${safe(label)}:</strong> ${safe(value)}</p>`).join('')}`
        : '';
      const emailHtml = `<h2>🚨 New Cascade Painting estimate request</h2>
        <p><strong>Name:</strong> ${safe(lead.name)}</p>
        <p><strong>Phone:</strong> ${safe(lead.phone)}</p>
        <p><strong>Email:</strong> ${safe(lead.email)}</p>
        <p><strong>Project:</strong> ${safe(lead.projectType)}</p>
        <p><strong>Location:</strong> ${safe(lead.location)}</p>
        <p><strong>Timing:</strong> ${safe(lead.timing)}</p>
        <p><strong>Details:</strong><br>${safe(lead.details).replace(/\n/g, '<br>')}</p>
        ${attributionHtml}
        <p><small>Lead ID: ${safe(lead.id)}</small></p>`;
      const response = await fetch('https://api.resend.com/emails', {
        method: 'POST',
        headers: { 'content-type': 'application/json', 'authorization': `Bearer ${env.RESEND_API_KEY}` },
        body: JSON.stringify({
          from: env.LEAD_FROM_EMAIL,
          to: [env.LEAD_TO_EMAIL],
          reply_to: lead.email,
          subject: `🚨 NEW WEBSITE REQUEST — ${lead.projectType} — ${lead.name}`,
          headers: { 'X-Priority': '1', 'Importance': 'high' },
          html: emailHtml,
          text: [
            'New Cascade Painting website estimate request',
            '',
            `Name: ${lead.name}`,
            `Phone: ${lead.phone}`,
            `Email: ${lead.email}`,
            `Project: ${lead.projectType}`,
            `Location: ${lead.location}`,
            `Timing: ${lead.timing}`,
            '',
            'Details:',
            lead.details,
            '',
            `Lead ID: ${lead.id}`,
            ...attributionRows.map(([label, value]) => `${label}: ${value}`)
          ].join('\n')
        })
      });
      if (!response.ok) throw new Error('email_failed');
      successes.push('email');
    } catch (_) { failures.push('email'); }
  }

  if (!successes.length) return json({ ok: false, error: 'delivery_not_configured' }, 503);
  return json({ ok: true, id: lead.id, delivered: successes, warning: failures.length ? failures : undefined }, 201);
}

export function onRequestGet() {
  return json({ ok: false, error: 'method_not_allowed' }, 405);
}
