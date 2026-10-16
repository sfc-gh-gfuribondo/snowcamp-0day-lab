// Progressive enhancement: content, downloads, and anchors work without JavaScript.
(function () {
  'use strict';

  const contents = document.querySelector('.contents');
  const toggle = document.querySelector('.contents-toggle');
  const navigation = document.getElementById('contents-links');
  const mobile = window.matchMedia('(max-width: 980px)');
  const sections = Array.from(document.querySelectorAll('main .step'));
  const links = Array.from(navigation.querySelectorAll('a'));
  const status = document.getElementById('copy-status');

  function setExpanded(expanded) {
    toggle.setAttribute('aria-expanded', String(expanded));
    navigation.hidden = !expanded;
  }

  function syncNavigation() {
    const focused = document.activeElement;
    toggle.hidden = !mobile.matches;
    setExpanded(!mobile.matches);
    if (mobile.matches && navigation.contains(focused)) toggle.focus();
    if (!mobile.matches && focused === toggle) links[0].focus();
  }

  contents.classList.add('is-enhanced');
  syncNavigation();
  mobile.addEventListener('change', syncNavigation);
  toggle.addEventListener('click', function () {
    setExpanded(toggle.getAttribute('aria-expanded') !== 'true');
  });
  contents.addEventListener('keydown', function (event) {
    if (event.key === 'Escape' && mobile.matches) {
      setExpanded(false);
      toggle.focus();
    }
  });

  document.querySelectorAll('a[href^="#"]').forEach(function (link) {
    link.addEventListener('click', function (event) {
      if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || event.button !== 0) return;
      const target = document.getElementById(link.getAttribute('href').slice(1));
      if (!target) return;
      event.preventDefault();
      if (mobile.matches && navigation.contains(link)) setExpanded(false);
      // Preserve deep links without a host webview reloading the page for a fragment.
      if (location.hash !== link.getAttribute('href')) history.pushState(null, '', link.getAttribute('href'));
      target.scrollIntoView({ block: 'start' });
      const focusTarget = target.querySelector('h2') || target;
      if (!focusTarget.hasAttribute('tabindex')) focusTarget.setAttribute('tabindex', '-1');
      focusTarget.focus({ preventScroll: true });
      scheduleHighlight();
    });
  });

  let current = '';
  let queued = false;
  function highlightSection() {
    queued = false;
    let active = sections[0];
    for (const section of sections) {
      if (section.getBoundingClientRect().top <= 120) active = section;
    }
    if (window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 4) {
      active = sections[sections.length - 1];
    }
    if (active.id === current) return;
    current = active.id;
    links.forEach(function (link) {
      if (link.getAttribute('href') === '#' + current) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });
  }
  function scheduleHighlight() {
    if (!queued) {
      queued = true;
      window.requestAnimationFrame(highlightSection);
    }
  }
  window.addEventListener('scroll', scheduleHighlight, { passive: true });
  window.addEventListener('resize', scheduleHighlight);
  function restoreAnchor() {
    const target = document.getElementById(location.hash.slice(1));
    if (target) {
      window.requestAnimationFrame(function () {
        target.scrollIntoView({ block: 'start', behavior: 'instant' });
        scheduleHighlight();
      });
    } else {
      scheduleHighlight();
    }
  }
  window.addEventListener('hashchange', restoreAnchor);
  window.addEventListener('popstate', restoreAnchor);
  window.addEventListener('load', restoreAnchor);
  document.querySelectorAll('details').forEach(function (details) {
    details.addEventListener('toggle', scheduleHighlight);
  });
  highlightSection();

  document.querySelectorAll('.code').forEach(function (block, index) {
    const pre = block.querySelector('pre');
    const prompt = Boolean(block.closest('.coco-practice'));
    const kind = prompt ? 'Prompt' : pre.textContent.startsWith('https://') ? 'Repository URL'
      : /^(import streamlit|st\.subheader)/.test(pre.textContent) ? 'Python' : 'SQL';
    const sectionName = block.closest('.step').dataset.title;
    const label = document.createElement('span');
    label.className = 'code-label';
    label.textContent = kind.toUpperCase();
    label.setAttribute('aria-hidden', 'true');
    const button = document.createElement('button');
    button.className = 'copy-btn';
    button.type = 'button';
    button.textContent = 'Copy';
    button.setAttribute('aria-label', `Copy ${kind.toLowerCase()} ${index + 1}: ${sectionName}`);
    pre.tabIndex = 0;
    pre.setAttribute('aria-label', `${kind}: ${sectionName}`);
    block.classList.add('has-copy');
    block.append(label, button);
    let resetTimer;

    button.addEventListener('click', async function () {
      window.clearTimeout(resetTimer);
      button.disabled = true;
      status.textContent = '';
      try {
        if (!navigator.clipboard || !navigator.clipboard.writeText) throw new Error('Clipboard unavailable');
        await navigator.clipboard.writeText(pre.textContent);
        button.textContent = 'Copied';
        button.classList.remove('copy-failed');
        status.textContent = `${kind} copied from ${sectionName}.`;
      } catch (_error) {
        const selection = window.getSelection();
        const range = document.createRange();
        range.selectNodeContents(pre);
        selection.removeAllRanges();
        selection.addRange(range);
        pre.focus({ preventScroll: true });
        button.textContent = 'Text selected';
        button.classList.add('copy-failed');
        status.textContent = 'Clipboard unavailable. Text selected; press Control+C or Command+C to copy.';
      } finally {
        button.disabled = false;
        resetTimer = window.setTimeout(function () {
          button.textContent = 'Copy';
          button.classList.remove('copy-failed');
        }, 2500);
      }
    });
  });
})();