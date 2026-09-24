(() => {
  'use strict';

  const qs = (s, r = document) => r.querySelector(s);
  const qsa = (s, r = document) => [...r.querySelectorAll(s)];

  qsa('[data-year]').forEach(el => { el.textContent = new Date().getFullYear(); });

  // Lightweight, privacy-conscious attribution handoff. No analytics library is required.
  const attributionKey = 'cascade_attribution';
  const currentParams = new URLSearchParams(location.search);
  const currentAttribution = {
    landingPage: location.href.slice(0, 1000),
    referrer: document.referrer.slice(0, 1000),
    utmSource: (currentParams.get('utm_source') || '').slice(0, 180),
    utmMedium: (currentParams.get('utm_medium') || '').slice(0, 180),
    utmCampaign: (currentParams.get('utm_campaign') || '').slice(0, 240),
    utmContent: (currentParams.get('utm_content') || '').slice(0, 240),
    utmTerm: (currentParams.get('utm_term') || '').slice(0, 240),
    gclid: (currentParams.get('gclid') || '').slice(0, 300)
  };
  try {
    const stored = JSON.parse(sessionStorage.getItem(attributionKey) || 'null');
    const hasCampaign = currentAttribution.utmSource || currentAttribution.utmMedium || currentAttribution.utmCampaign || currentAttribution.gclid;
    if (!stored || hasCampaign) sessionStorage.setItem(attributionKey, JSON.stringify(currentAttribution));
  } catch (_) {}

  const track = (event, detail = {}) => {
    try {
      if (Array.isArray(window.dataLayer)) window.dataLayer.push({ event, ...detail });
      window.dispatchEvent(new CustomEvent('cascade:conversion', { detail: { event, ...detail } }));
    } catch (_) {}
  };
  qsa('a[href^="tel:"]').forEach(link => link.addEventListener('click', () => track('phone_click')));
  qsa('a[href$="estimate/"],a[href*="/estimate/"]').forEach(link => link.addEventListener('click', () => track('estimate_cta_click', { href: link.getAttribute('href') })));

  const header = qs('[data-header]');
  const onScroll = () => header?.classList.toggle('is-scrolled', window.scrollY > 18);
  onScroll();
  addEventListener('scroll', onScroll, { passive: true });

  // Accessible mobile navigation.
  const toggle = qs('[data-menu-toggle]');
  const menu = qs('[data-mobile-menu]');
  const closeMenu = ({ restoreFocus = false } = {}) => {
    if (!menu || !toggle) return;
    menu.classList.remove('is-open');
    menu.setAttribute('aria-hidden', 'true');
    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-label', 'Open menu');
    document.body.style.overflow = '';
    if (restoreFocus) toggle.focus();
  };
  const openMenu = () => {
    if (!menu || !toggle) return;
    menu.classList.add('is-open');
    menu.setAttribute('aria-hidden', 'false');
    toggle.setAttribute('aria-expanded', 'true');
    toggle.setAttribute('aria-label', 'Close menu');
    document.body.style.overflow = 'hidden';
    qs('a', menu)?.focus({ preventScroll: true });
  };
  toggle?.addEventListener('click', () => {
    toggle.getAttribute('aria-expanded') === 'true' ? closeMenu() : openMenu();
  });
  qsa('a', menu || document).forEach(a => a.addEventListener('click', () => closeMenu()));
  addEventListener('keydown', e => {
    if (e.key === 'Escape' && menu?.classList.contains('is-open')) closeMenu({ restoreFocus: true });
  });
  addEventListener('resize', () => {
    if (innerWidth > 900 && menu?.classList.contains('is-open')) closeMenu();
  }, { passive: true });

  // Project reel controls.
  const reel = qs('[data-project-reel]');
  const shiftReel = dir => {
    if (!reel) return;
    const card = qs('.reel-card', reel);
    reel.scrollBy({ left: dir * ((card?.getBoundingClientRect().width || 420) + 18), behavior: 'smooth' });
  };
  qs('[data-reel-prev]')?.addEventListener('click', () => shiftReel(-1));
  qs('[data-reel-next]')?.addEventListener('click', () => shiftReel(1));

  // Interactive service preview. Each service declares the responsive assets it actually has.
  const preview = qs('[data-service-preview]');
  const previewImg = qs('.service-preview-img', preview || document);
  const previewCaption = qs('[data-service-caption]', preview || document);
  const setPreview = row => {
    if (!preview || !previewImg) return;
    const src = row.dataset.serviceSrc;
    const srcset = row.dataset.serviceSrcset;
    if (!src) return;

    qsa('[data-service-src]').forEach(r => r.classList.remove('is-active'));
    row.classList.add('is-active');
    preview.classList.add('is-swapping');

    const probe = new Image();
    probe.onload = () => {
      previewImg.src = src;
      if (srcset) previewImg.srcset = srcset;
      else previewImg.removeAttribute('srcset');
      previewImg.alt = `${row.dataset.serviceLabel || 'Painting'} project by Cascade Painting`;
      if (previewCaption) previewCaption.textContent = row.dataset.serviceLabel || 'Cascade Painting';
      requestAnimationFrame(() => preview.classList.remove('is-swapping'));
    };
    probe.onerror = () => preview.classList.remove('is-swapping');
    probe.src = src;
  };
  qsa('[data-service-src]').forEach(row => {
    row.addEventListener('mouseenter', () => setPreview(row));
    row.addEventListener('focus', () => setPreview(row));
  });

  // Progressive reveal. Content stays visible when JS or IntersectionObserver is unavailable.
  qsa('section > .wrap, .project-story-grid article, .service-overview-card, .standard-page-grid article').forEach(el => {
    if (el.closest('.hero-home,.page-hero,.estimate-hero')) return;
    el.setAttribute('data-reveal', '');
  });
  if ('IntersectionObserver' in window) {
    const revealObserver = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          revealObserver.unobserve(entry.target);
        }
      });
    }, { threshold: .08, rootMargin: '0px 0px -5%' });
    qsa('[data-reveal]').forEach(el => revealObserver.observe(el));
  } else {
    qsa('[data-reveal]').forEach(el => el.classList.add('is-visible'));
  }

  // Multi-step estimate form with native validity checks and a same-origin API handoff.
  const form = qs('[data-estimate-form]');
  if (form) {
    let step = 1;
    const status = qs('[data-form-status]', form);
    const success = qs('[data-form-success]', form);

    const setStatus = message => { if (status) status.textContent = message || ''; };
    const showStep = n => {
      step = Math.max(1, Math.min(3, n));
      qsa('[data-step]', form).forEach(section => section.classList.toggle('is-active', Number(section.dataset.step) === step));
      qsa('[data-step-dot]', form).forEach(dot => dot.classList.toggle('is-active', Number(dot.dataset.stepDot) <= step));
      setStatus('');
      form.scrollIntoView({ behavior: 'smooth', block: 'center' });
    };

    const stepValid = n => {
      const section = qs(`[data-step="${n}"]`, form);
      if (!section) return false;
      const required = qsa('[required]', section);
      let firstInvalid = null;

      required.forEach(field => {
        let valid = field.checkValidity();
        if (field.type === 'radio') {
          valid = Boolean(qs(`[name="${CSS.escape(field.name)}"]:checked`, section));
        }
        field.setAttribute('aria-invalid', valid ? 'false' : 'true');
        if (!valid && !firstInvalid) firstInvalid = field;
      });

      if (firstInvalid) {
        setStatus('Please complete the highlighted field before continuing.');
        firstInvalid.focus({ preventScroll: true });
        firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
        return false;
      }
      return true;
    };

    qsa('input,select,textarea', form).forEach(field => {
      const clearInvalid = () => {
        if (field.checkValidity()) field.setAttribute('aria-invalid', 'false');
      };
      field.addEventListener('input', clearInvalid);
      field.addEventListener('change', clearInvalid);
    });

    qsa('[data-next]', form).forEach(button => button.addEventListener('click', () => {
      if (stepValid(step)) showStep(step + 1);
    }));
    qsa('[data-back]', form).forEach(button => button.addEventListener('click', () => showStep(step - 1)));

    const attribution = () => {
      let stored = {};
      try { stored = JSON.parse(sessionStorage.getItem(attributionKey) || '{}') || {}; } catch (_) {}
      return {
        sourcePage: location.href.slice(0, 1000),
        landingPage: String(stored.landingPage || location.href).slice(0, 1000),
        referrer: String(stored.referrer || document.referrer || '').slice(0, 1000),
        utmSource: String(stored.utmSource || '').slice(0, 180),
        utmMedium: String(stored.utmMedium || '').slice(0, 180),
        utmCampaign: String(stored.utmCampaign || '').slice(0, 240),
        utmContent: String(stored.utmContent || '').slice(0, 240),
        utmTerm: String(stored.utmTerm || '').slice(0, 240),
        gclid: String(stored.gclid || '').slice(0, 300)
      };
    };

    const mailFallback = data => {
      const subject = encodeURIComponent(`Website estimate request — ${data.projectType || 'Painting project'}`);
      const body = encodeURIComponent(`Name: ${data.name}\nPhone: ${data.phone}\nEmail: ${data.email}\nProject: ${data.projectType}\nLocation: ${data.location}\nTiming: ${data.timing}\n\nDetails:\n${data.details}`);
      setStatus('The secure form service is temporarily unavailable. Your mail app will open with the project details prefilled.');
      setTimeout(() => { location.href = `mailto:paxton@cascadepaintingpa.com?subject=${subject}&body=${body}`; }, 250);
    };

    form.addEventListener('submit', async event => {
      event.preventDefault();
      if (!stepValid(3)) return;

      const button = qs('[type="submit"]', form);
      const data = { ...Object.fromEntries(new FormData(form).entries()), ...attribution() };
      if (data.website) return;

      setStatus('Sending your project details…');
      if (button) button.disabled = true;

      try {
        const response = await fetch('/api/lead', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
          body: JSON.stringify(data)
        });
        let result = {};
        try { result = await response.json(); } catch (_) {}

        if (response.ok && result.ok !== false) {
          form.reset();
          track('lead_submit_success', { leadId: result.id || '', projectType: data.projectType || '' });
          qsa('[data-step], .form-progress', form).forEach(el => { el.hidden = true; });
          if (success) success.hidden = false;
          setStatus('');
          success?.scrollIntoView({ behavior: 'smooth', block: 'center' });
          return;
        }

        if (response.status === 400 || response.status === 403 || response.status === 413 || response.status === 415) {
          setStatus('We could not send that request yet. Please check your contact information and project details, then try again.');
          return;
        }
        mailFallback(data);
      } catch (_) {
        mailFallback(data);
      } finally {
        if (button) button.disabled = false;
      }
    });
  }

  // V4 PRODUCTION OPTIMIZATION
  // First-party, session-scoped measurement. No cross-site ID, no fingerprinting, no ad profile.
  const sessionKey = 'cascade_session_id';
  let sessionId = '';
  try {
    sessionId = sessionStorage.getItem(sessionKey) || crypto.randomUUID();
    sessionStorage.setItem(sessionKey, sessionId);
  } catch (_) {}
  const firstPartyEvent = (event, detail = {}) => {
    if (!['cascadepaintingpa.com','www.cascadepaintingpa.com'].includes(location.hostname)) return;
    const payload = {
      event,
      sessionId,
      path: location.pathname.slice(0, 500),
      referrer: document.referrer.slice(0, 1000),
      detail,
      ts: new Date().toISOString()
    };
    const body = JSON.stringify(payload);
    try {
      if (navigator.sendBeacon) {
        const blob = new Blob([body], { type: 'application/json' });
        if (navigator.sendBeacon('/api/event', blob)) return;
      }
      fetch('/api/event', { method:'POST', headers:{'Content-Type':'application/json'}, body, keepalive:true }).catch(() => {});
    } catch (_) {}
  };

  const idle = window.requestIdleCallback || (cb => setTimeout(cb, 900));
  idle(() => firstPartyEvent('page_view', { title: document.title.slice(0, 180) }));

  qsa('a[href^="mailto:"]').forEach(link => link.addEventListener('click', () => firstPartyEvent('email_click')));
  qsa('a[href*="google.com/maps"]').forEach(link => link.addEventListener('click', () => firstPartyEvent('google_profile_click')));
  qsa('a[href^="/projects/"]').forEach(link => link.addEventListener('click', () => firstPartyEvent('project_view_click', { href: link.getAttribute('href') })));
  qsa('a[href^="/resources/"]').forEach(link => link.addEventListener('click', () => firstPartyEvent('resource_click', { href: link.getAttribute('href') })));
  qsa('a[href^="tel:"]').forEach(link => link.addEventListener('click', () => firstPartyEvent('phone_click')));
  qsa('a[href*="/estimate/"]').forEach(link => link.addEventListener('click', () => firstPartyEvent('estimate_cta_click', { href: link.getAttribute('href') })));

  // Measure meaningful scroll depth once per page.
  const scrollMarks = new Set();
  const onDepth = () => {
    const max = Math.max(1, document.documentElement.scrollHeight - innerHeight);
    const pct = Math.round((scrollY / max) * 100);
    [50,90].forEach(mark => {
      if (pct >= mark && !scrollMarks.has(mark)) {
        scrollMarks.add(mark);
        firstPartyEvent('scroll_depth', { percent: mark });
      }
    });
  };
  addEventListener('scroll', onDepth, { passive:true });

  // Make the estimate experience resilient: prefill service context and keep an in-session draft.
  if (form) {
    const draftKey = 'cascade_estimate_draft';
    const serviceFromUrl = new URLSearchParams(location.search).get('service');
    const serviceFromReferrer = (() => {
      try {
        const path = new URL(document.referrer).pathname;
        const map = {
          '/interior-painting-lansdale-pa/':'Interior Painting',
          '/exterior-painting-lansdale-pa/':'Exterior Painting',
          '/cabinet-refinishing-lansdale-pa/':'Cabinet Refinishing',
          '/wallpaper-removal-drywall-repair/':'Drywall / Wallpaper',
          '/floor-coatings-lansdale-pa/':'Floor Coating',
          '/commercial-painting-lansdale-pa/':'Commercial'
        };
        return map[path] || '';
      } catch (_) { return ''; }
    })();
    const allowedServices = ['Interior Painting','Exterior Painting','Cabinet Refinishing','Drywall / Wallpaper','Floor Coating','Commercial'];
    const desiredService = allowedServices.includes(serviceFromUrl) ? serviceFromUrl : serviceFromReferrer;
    if (desiredService) {
      const radio = qs(`input[name="projectType"][value="${CSS.escape(desiredService)}"]`, form);
      if (radio) radio.checked = true;
    }

    try {
      const draft = JSON.parse(sessionStorage.getItem(draftKey) || '{}');
      Object.entries(draft).forEach(([name,value]) => {
        if (name === 'consent' || name === 'website') return;
        const fields = qsa(`[name="${CSS.escape(name)}"]`, form);
        fields.forEach(field => {
          if (field.type === 'radio') field.checked = field.value === value;
          else if (!field.value) field.value = value;
        });
      });
    } catch (_) {}

    const saveDraft = () => {
      const data = {};
      qsa('input,select,textarea', form).forEach(field => {
        if (!field.name || ['consent','website'].includes(field.name)) return;
        if (field.type === 'radio') { if (field.checked) data[field.name] = field.value; }
        else data[field.name] = field.value;
      });
      try { sessionStorage.setItem(draftKey, JSON.stringify(data)); } catch (_) {}
    };
    qsa('input,select,textarea', form).forEach(field => {
      field.addEventListener('change', saveDraft);
      if (field.tagName === 'TEXTAREA' || field.type === 'text' || field.type === 'email' || field.type === 'tel') field.addEventListener('input', saveDraft);
    });
    qsa('[data-next]', form).forEach(button => button.addEventListener('click', () => firstPartyEvent('estimate_step_continue', { step })));
    form.addEventListener('submit', () => firstPartyEvent('estimate_submit_attempt'));
    window.addEventListener('cascade:conversion', event => {
      if (event.detail?.event === 'lead_submit_success') {
        try { sessionStorage.removeItem(draftKey); } catch (_) {}
        firstPartyEvent('lead_submit_success', { projectType: event.detail.projectType || '' });
      }
    });
  }

  // Warm the estimate page after the critical rendering path so a later CTA feels instant.
  idle(() => {
    if (!location.pathname.startsWith('/estimate')) {
      const prefetch = document.createElement('link');
      prefetch.rel = 'prefetch';
      prefetch.href = '/estimate/';
      document.head.appendChild(prefetch);
    }
  });
})();
