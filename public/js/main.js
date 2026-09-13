const header = document.querySelector('[data-header]');
const toggle = document.querySelector('[data-menu-toggle]');
const menu = document.querySelector('[data-mobile-menu]');
const backdrop = document.querySelector('[data-menu-backdrop]');

const closeMenu = () => {
  if (!toggle || !menu) return;
  toggle.setAttribute('aria-expanded', 'false');
  toggle.setAttribute('aria-label', 'Open menu');
  menu.classList.remove('open');
  backdrop?.classList.remove('open');
  backdrop?.setAttribute('aria-hidden', 'true');
  document.body.classList.remove('menu-open');
};

const openMenu = () => {
  if (!toggle || !menu) return;
  toggle.setAttribute('aria-expanded', 'true');
  toggle.setAttribute('aria-label', 'Close menu');
  menu.classList.add('open');
  backdrop?.classList.add('open');
  backdrop?.setAttribute('aria-hidden', 'false');
  document.body.classList.add('menu-open');
};

if (toggle && menu) {
  toggle.addEventListener('click', () => {
    const open = toggle.getAttribute('aria-expanded') === 'true';
    open ? closeMenu() : openMenu();
  });

  menu.querySelectorAll('a').forEach(link => link.addEventListener('click', closeMenu));
  backdrop?.addEventListener('click', closeMenu);
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') closeMenu();
  });
}

window.addEventListener('scroll', () => {
  header?.classList.toggle('scrolled', window.scrollY > 20);
}, { passive: true });

const reveals = document.querySelectorAll('.reveal');
if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('in-view');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });
  reveals.forEach(el => observer.observe(el));
} else {
  reveals.forEach(el => el.classList.add('in-view'));
}

const trackAnalyticsEvent = (eventName, params = {}) => {
  if (typeof window.gtag !== 'function') return;
  window.gtag('event', eventName, params);
};

// Track clicks on any phone link as a lead action. On mobile, opening the
// phone app can move the browser to the background before Analytics has time
// to send the event, so briefly hold navigation and use a callback/fallback.
document.addEventListener('click', event => {
  const phoneLink = event.target.closest('a[href^="tel:"]');
  if (!phoneLink) return;

  if (typeof window.gtag !== 'function') return;

  event.preventDefault();
  const phoneHref = phoneLink.href;
  let navigated = false;

  const continueToPhone = () => {
    if (navigated) return;
    navigated = true;
    window.location.href = phoneHref;
  };

  window.gtag('event', 'phone_call_click', {
    method: 'phone',
    link_text: phoneLink.textContent.trim().replace(/\s+/g, ' ').slice(0, 100),
    transport_type: 'beacon',
    event_callback: continueToPhone,
    event_timeout: 800
  });

  // Never make the visitor wait if Analytics is slow or blocked.
  window.setTimeout(continueToPhone, 900);
});

const form = document.getElementById('estimate-form');
const status = document.querySelector('[data-form-status]');

form?.addEventListener('submit', event => {
  event.preventDefault();
  const required = [...form.querySelectorAll('[required]')];
  let valid = true;

  required.forEach(field => {
    const fieldValid = field.checkValidity();
    field.setAttribute('aria-invalid', String(!fieldValid));
    if (!fieldValid) valid = false;
  });

  if (!valid) {
    status.textContent = 'Please complete the required fields before sending.';
    form.querySelector('[aria-invalid="true"]')?.focus();
    return;
  }

  const data = new FormData(form);
  const subject = `Website estimate request — ${data.get('projectType')}`;
  const body = [
    'New estimate request from cascadepaintingpa.com',
    '',
    `Name: ${data.get('firstName')} ${data.get('lastName')}`,
    `Email: ${data.get('email')}`,
    `Phone: ${data.get('phone') || 'Not provided'}`,
    `Project type: ${data.get('projectType')}`,
    `City / ZIP: ${data.get('location') || 'Not provided'}`,
    '',
    'Project details:',
    data.get('message') || 'No additional details provided.'
  ].join('\n');

  // Do not send names, email addresses, phone numbers, or other user-entered
  // personal information to Google Analytics. This event records only the
  // successful estimate-form action and the selected project type.
  trackAnalyticsEvent('generate_lead', {
    method: 'estimate_form',
    project_type: String(data.get('projectType') || 'unknown')
  });

  status.textContent = 'Opening your email app with the project details prepared…';
  window.location.href = `mailto:paxton@cascadepaintingpa.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
});
