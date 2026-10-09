// Step navigation (hash-based) and copy-to-clipboard for code blocks.
(function () {
  const steps = Array.from(document.querySelectorAll('section.step'));
  const nav = document.querySelector('nav.steps');
  const list = nav.querySelector('ol');

  // Build the left nav from the sections so titles live in one place.
  steps.forEach(function (s) {
    const li = document.createElement('li');
    const a = document.createElement('a');
    a.href = '#' + s.id;
    a.textContent = s.dataset.title;
    const mins = document.createElement('span');
    mins.className = 'mins';
    mins.textContent = s.dataset.mins + ' min';
    a.appendChild(mins);
    li.appendChild(a);
    list.appendChild(li);
  });
  const links = Array.from(list.querySelectorAll('a'));

  // Prev/next buttons at the bottom of each step.
  steps.forEach(function (s, i) {
    const pager = document.createElement('div');
    pager.className = 'pager';
    const prev = document.createElement('a');
    prev.className = 'prev';
    const next = document.createElement('a');
    next.className = 'next';
    if (i > 0) { prev.href = '#' + steps[i - 1].id; prev.textContent = '\u2190 ' + steps[i - 1].dataset.title; }
    else { prev.hidden = true; prev.textContent = '.'; }
    if (i < steps.length - 1) { next.href = '#' + steps[i + 1].id; next.textContent = steps[i + 1].dataset.title + ' \u2192'; }
    else { next.hidden = true; next.textContent = '.'; }
    pager.appendChild(prev);
    pager.appendChild(next);
    s.appendChild(pager);
  });

  function show() {
    const id = location.hash.slice(1);
    const target = steps.find(function (s) { return s.id === id; }) || steps[0];
    steps.forEach(function (s) { s.classList.toggle('active', s === target); });
    links.forEach(function (a) { a.classList.toggle('active', a.getAttribute('href') === '#' + target.id); });
    nav.classList.remove('open');
    window.scrollTo(0, 0);
  }
  window.addEventListener('hashchange', show);
  show();

  document.querySelector('.menu-btn').addEventListener('click', function () {
    nav.classList.toggle('open');
  });

  // Copy buttons.
  document.querySelectorAll('.code').forEach(function (block) {
    const btn = document.createElement('button');
    btn.className = 'copy-btn';
    btn.type = 'button';
    btn.textContent = 'Copy';
    btn.addEventListener('click', function () {
      const text = block.querySelector('pre').innerText;
      navigator.clipboard.writeText(text).then(function () {
        btn.textContent = 'Copied!';
        setTimeout(function () { btn.textContent = 'Copy'; }, 1500);
      });
    });
    block.appendChild(btn);
  });
})();
