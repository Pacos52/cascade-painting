(() => {
  'use strict';

  const sections = [...document.querySelectorAll('[data-google-reviews]')];
  if (!sections.length) return;

  const dateFormat = new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  const countFormat = new Intl.NumberFormat('en-US');
  const fallback = 'Reviews are temporarily unavailable here. Read customer feedback on Google.';

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function safeUrl(value, photo = false) {
    if (typeof value !== 'string') return null;
    try {
      const url = new URL(value);
      if (url.protocol !== 'https:' || url.username || url.password || url.port) return null;
      const host = url.hostname;
      const allowed = photo
        ? ['googleusercontent.com', 'ggpht.com'].some(domain => host === domain || host.endsWith(`.${domain}`))
        : host === 'maps.google.com' || host === 'maps.app.goo.gl'
          || (['google.com', 'www.google.com'].includes(host) && /^\/maps(?:\/|$)/.test(url.pathname));
      return allowed ? url.href : null;
    } catch {
      return null;
    }
  }

  function reviewDate(review) {
    const value = review.updateTime || review.createTime;
    const parsed = typeof value === 'string' ? new Date(value) : null;
    return parsed && Number.isFinite(parsed.getTime()) ? parsed : null;
  }

  function reviewCard(review) {
    const item = element('li', 'google-review-item');
    const card = element('article', 'google-live-review');
    const author = typeof review.reviewer?.displayName === 'string' && review.reviewer.displayName.trim()
      ? review.reviewer.displayName.trim() : 'Google reviewer';
    const heading = element('div', 'google-review-author');
    const avatar = element('span', 'google-review-avatar', Array.from(author)[0].toUpperCase());
    avatar.setAttribute('aria-hidden', 'true');
    const photoUrl = safeUrl(review.reviewer?.profilePhotoUrl, true);
    if (photoUrl) {
      const photo = element('img');
      photo.alt = '';
      photo.width = 40;
      photo.height = 40;
      photo.loading = 'lazy';
      photo.decoding = 'async';
      photo.referrerPolicy = 'no-referrer';
      photo.addEventListener('error', () => photo.remove(), { once: true });
      photo.src = photoUrl;
      avatar.append(photo);
    }
    const byline = element('div', 'google-review-byline');
    byline.append(element('h3', 'google-review-name', author));
    const date = reviewDate(review);
    if (date) {
      const updated = review.createTime && review.updateTime && review.createTime !== review.updateTime;
      const time = element('time', 'google-review-date', `${updated ? 'Updated ' : ''}${dateFormat.format(date)}`);
      time.dateTime = date.toISOString();
      byline.append(time);
    }
    heading.append(avatar, byline);
    const rating = element('div', 'google-review-rating', '★'.repeat(review.starRating) + '☆'.repeat(5 - review.starRating));
    rating.setAttribute('role', 'img');
    rating.setAttribute('aria-label', `${review.starRating} out of 5 stars`);
    const comment = typeof review.comment === 'string' ? review.comment.trim() : '';
    card.append(heading, rating, element('p', 'google-review-comment', comment || 'This customer left a star rating without a written review.'));
    card.append(element('span', 'google-review-source', 'Posted on Google'));
    item.append(card);
    return item;
  }

  function setStatus(section, message) {
    section.querySelector('[data-reviews-status]').textContent = message;
    section.querySelector('[data-reviews-list]').setAttribute('aria-busy', 'false');
  }

  function render(section, data) {
    const list = section.querySelector('[data-reviews-list]');
    const limit = Math.min(12, Math.max(1, Number(section.dataset.reviewLimit) || 3));
    const reviews = data.reviews.filter(review => review && Number.isInteger(review.starRating)
      && review.starRating >= 1 && review.starRating <= 5)
      .sort((a, b) => (reviewDate(b)?.getTime() || 0) - (reviewDate(a)?.getTime() || 0))
      .slice(0, limit);
    const mapsUrl = safeUrl(data.googleMapsUrl);
    if (mapsUrl) section.querySelectorAll('[data-review-link]').forEach(link => { link.href = mapsUrl; });

    const count = data.totalReviewCount;
    const average = data.averageRating;
    if (Number.isSafeInteger(count) && count > 0 && Number.isFinite(average) && average >= 1 && average <= 5) {
      const rating = average.toFixed(1);
      const total = `${countFormat.format(count)} Google ${count === 1 ? 'review' : 'reviews'}`;
      section.querySelector('[data-review-summary]').textContent = `${rating} out of 5 on Google`;
      section.querySelector('[data-review-summary-detail]').textContent = `Based on ${total}.`;
      document.querySelectorAll('[data-review-hero-rating]').forEach(node => {
        node.textContent = `${rating} / 5`;
        node.setAttribute('aria-label', `${rating} out of 5 stars on Google`);
        node.hidden = false;
      });
      document.querySelectorAll('[data-review-hero-count]').forEach(node => { node.textContent = total; });
    }

    list.replaceChildren(...reviews.map(reviewCard));
    list.hidden = reviews.length === 0;
    if (data.status === 'stale') {
      setStatus(section, 'Showing previously loaded Google feedback. Visit Google for the latest reviews.');
    } else if (!reviews.length) {
      setStatus(section, 'No Google reviews are available to display here yet. Visit our public listing on Google.');
    } else {
      setStatus(section, 'Recent customer reviews from Google.');
    }
  }

  async function loadReviews() {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);
    sections.forEach(section => {
      section.querySelector('[data-reviews-status]').textContent = 'Loading recent Google reviews…';
      section.querySelector('[data-reviews-list]').setAttribute('aria-busy', 'true');
    });
    try {
      // The same-origin endpoint owns caching and all Google credentials.
      const response = await fetch('/api/reviews', {
        headers: { Accept: 'application/json' }, credentials: 'omit', signal: controller.signal
      });
      if (!response.ok) throw new Error('Reviews unavailable');
      const data = await response.json();
      if (!data || !['ok', 'stale', 'empty'].includes(data.status) || !Array.isArray(data.reviews)) {
        throw new Error('Reviews unavailable');
      }
      sections.forEach(section => render(section, data));
    } catch {
      sections.forEach(section => setStatus(section, fallback));
    } finally {
      clearTimeout(timeout);
    }
  }

  loadReviews();
})();
