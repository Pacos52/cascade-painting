import { onRequestGet as healthGet } from '../functions/api/health.js';
import { onRequestGet as leadGet, onRequestPost as leadPost } from '../functions/api/lead.js';
import { onRequestGet as eventGet, onRequestPost as eventPost } from '../functions/api/event.js';
import {
  handleGoogleCallback,
  handleGoogleStart,
  handleGoogleStatus,
  handleReviews,
} from '../server/google-business.js';

const apiNotFound = () => Response.json(
  { ok: false, error: 'not_found' },
  {
    status: 404,
    headers: {
      'cache-control': 'no-store',
      'x-content-type-options': 'nosniff',
    },
  },
);

const methodNotAllowed = (allow) => new Response('Method not allowed', {
  status: 405,
  headers: {
    allow,
    'cache-control': 'no-store',
    'x-content-type-options': 'nosniff',
  },
});

function pagesContext(request, env, executionContext) {
  return {
    request,
    env,
    params: {},
    data: {},
    waitUntil: executionContext.waitUntil.bind(executionContext),
    passThroughOnException: executionContext.passThroughOnException.bind(executionContext),
  };
}

async function routeApi(request, env, executionContext) {
  const { pathname } = new URL(request.url);
  const context = pagesContext(request, env, executionContext);

  if (pathname === '/api/health') {
    return request.method === 'GET' ? healthGet(context) : methodNotAllowed('GET');
  }
  if (pathname === '/api/lead') {
    if (request.method === 'POST') return leadPost(context);
    if (request.method === 'GET') return leadGet(context);
    return methodNotAllowed('GET, POST');
  }
  if (pathname === '/api/event') {
    if (request.method === 'POST') return eventPost(context);
    if (request.method === 'GET') return eventGet(context);
    return methodNotAllowed('GET, POST');
  }
  if (pathname === '/api/reviews') return handleReviews(context);
  if (pathname === '/api/google/start') return handleGoogleStart(context);
  if (pathname === '/api/google/callback') return handleGoogleCallback(context);
  if (pathname === '/api/google/status') return handleGoogleStatus(context);

  return apiNotFound();
}

export default {
  async fetch(request, env, executionContext) {
    const url = new URL(request.url);

    if (url.hostname === 'www.cascadepaintingpa.com') {
      url.hostname = 'cascadepaintingpa.com';
      return Response.redirect(url.toString(), 308);
    }

    const pathname = url.pathname;

    if (pathname === '/api' || pathname.startsWith('/api/')) {
      return routeApi(request, env, executionContext);
    }

    return env.ASSETS.fetch(request);
  },
};
