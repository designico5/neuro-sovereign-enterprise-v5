/* ============================================================================
 * NSE-v5 · Sovereign Neural Observatory — Motion & Interaction module
 * ----------------------------------------------------------------------------
 * Vanilla JS (no libraries). A single IIFE that self-initializes on
 * DOMContentLoaded and is idempotent (window sentinel + data-motion-bound).
 *
 * It coexists with the legacy inline <script> left in index.html:
 *   - every DOM query is guarded with if(el),
 *   - every binding is namespaced (data-motion-*),
 *   - scroll-driven work is folded into ONE rAF-throttled handler,
 *   - IntersectionObserver is used for scrollspy / reveals / count-up.
 * A second load of this file (or the legacy script) will not double-bind.
 * ========================================================================== */
(function () {
  'use strict';

  var BOOT_FLAG = '__NSE_MOTION_V1__';

  function boot() {
    if (window[BOOT_FLAG]) return;          // IIFE-safe: boot at most once
    window[BOOT_FLAG] = true;

    var body = document.body;
    if (body) body.setAttribute('data-motion-bound', 'v1');

    var hasIO = 'IntersectionObserver' in window;
    var finePtr = matchMedia('(pointer: fine)').matches;
    var reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

    /* ---------- 0) inject the active-link style exactly once ---------- */
    if (document.head && !document.getElementById('nse-motion-style')) {
      var st = document.createElement('style');
      st.id = 'nse-motion-style';
      st.textContent =
        '.nav-links a.active{color:var(--gold-hi)}' +
        '.nav-links a.active::after{width:100%;background:linear-gradient(90deg,var(--gold),var(--cyan))}';
      document.head.appendChild(st);
    }

    /* ---------- 1) scrollspy (IntersectionObserver) ---------- */
    var SECTION_IDS = ['strata','layers','sovereignty','symbiosis','deploy',
                       'usecases','secmatrix','roadmap','genie','changelog','faq','start'];
    var navLinks = Array.prototype.slice.call(document.querySelectorAll('.nav-links a[href^="#"]'));
    var vis = {};

    function setActive(id) {
      for (var i = 0; i < navLinks.length; i++) {
        var on = navLinks[i].getAttribute('href') === '#' + id;
        navLinks[i].classList.toggle('active', on);
        if (on) navLinks[i].setAttribute('aria-current', 'true');
        else navLinks[i].removeAttribute('aria-current');
      }
    }
    function clearActive() {
      for (var i = 0; i < navLinks.length; i++) {
        navLinks[i].classList.remove('active');
        navLinks[i].removeAttribute('aria-current');
      }
    }

    if (hasIO && navLinks.length) {
      var spyIO = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) { vis[en.target.id] = en.isIntersecting; });
        var current = null;                       // deepest doc-order section in band
        for (var i = 0; i < SECTION_IDS.length; i++) if (vis[SECTION_IDS[i]]) current = SECTION_IDS[i];
        if (current) setActive(current); else clearActive();
      }, { rootMargin: '0px 0px -55% 0px', threshold: 0 });
      SECTION_IDS.forEach(function (id) {
        var el = document.getElementById(id);
        if (el && !el.dataset.motionSpy) { el.dataset.motionSpy = '1'; spyIO.observe(el); }
      });
    }

    /* ---------- 2 + 6 + 7) one rAF-throttled scroll handler ---------- */
    var progress = document.getElementById('progress');
    var nav = document.getElementById('nav');
    var top = document.getElementById('top');
    var heroCopy = top ? top.querySelector('.hero-copy') : document.querySelector('.hero-copy');
    var ticking = false;

    function updateScroll() {
      ticking = false;
      var doc = document.documentElement;
      var max = doc.scrollHeight - doc.clientHeight;
      var y = window.scrollY || doc.scrollTop || 0;

      if (progress) {                              // (2) progress bar
        var frac = max > 0 ? y / max : 0;
        progress.style.width = (Math.min(1, Math.max(0, frac)) * 100).toFixed(3) + '%';
      }
      if (nav) nav.classList.toggle('scrolled', y > 40);   // (6) nav style

      if (heroCopy && !reduced) {                  // (7) hero depth-fade
        var span = (window.innerHeight || 900) * 0.6;
        var t = Math.min(1, y / span);
        heroCopy.style.opacity = (1 - t * 0.85).toFixed(3);
        heroCopy.style.transform = 'translateY(' + (-t * 44).toFixed(2) + 'px)';
      }
    }
    function onScroll() {
      if (!ticking) { ticking = true; requestAnimationFrame(updateScroll); }
    }
    addEventListener('scroll', onScroll, { passive: true });
    addEventListener('resize', onScroll, { passive: true });
    updateScroll();

    /* ---------- 3) staggered reveals (IntersectionObserver) ---------- */
    if (hasIO) {
      var revIO = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) { en.target.classList.add('in'); revIO.unobserve(en.target); }
        });
      }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });
      document.querySelectorAll('.rv').forEach(function (el) {
        if (!el.dataset.motionRv) { el.dataset.motionRv = '1'; revIO.observe(el); }
      });
    }

    /* ---------- 4) count-up (ease-out cubic, ~1.6s) ---------- */
    if (hasIO) {
      function countUp(el) {
        var target = parseFloat(el.dataset.count || el.textContent || '0') || 0;
        var dec = parseInt(el.dataset.dec || '0', 10) || 0;
        var s0 = performance.now();
        (function step(now) {
          var p = Math.min(1, (now - s0) / 1600);
          var eased = 1 - Math.pow(1 - p, 3);
          el.textContent = (target * eased).toFixed(dec);
          if (p < 1) requestAnimationFrame(step); else el.textContent = target.toFixed(dec);
        })(s0);
      }
      var countIO = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (!en.isIntersecting) return;
          var el = en.target;
          countIO.unobserve(el);
          // if the legacy script already drove it to the final value, don't re-run
          if (parseFloat(el.textContent) === parseFloat(el.dataset.count || '0')) return;
          countUp(el);
        });
      }, { threshold: 0.6 });
      document.querySelectorAll('[data-count]').forEach(function (el) {
        if (!el.dataset.motionCount) { el.dataset.motionCount = '1'; countIO.observe(el); }
      });
    }

    /* ---------- 5) magnetic hover (fine pointers only) ---------- */
    if (finePtr && !reduced) {
      var magEls = Array.prototype.slice.call(document.querySelectorAll('.mag'));
      var magPending = {};   // {id: clientX/Y} — layout read happens ONCE on enter
      var magRaf = null;
      magEls.forEach(function (el, i) {
        if (el.dataset.motionMag) return;
        el.dataset.motionMag = '1';
        // cache rect on enter (single layout read), not on every mousemove
        el.addEventListener('mouseenter', function () {
          el._magRect = el.getBoundingClientRect();
          el._magId = i;
        });
        el.addEventListener('mousemove', function (e) {
          if (!el._magRect) return;
          magPending[i] = { x: e.clientX, y: e.clientY, el: el };
          if (!magRaf) magRaf = requestAnimationFrame(function () {
            magRaf = null;
            for (var k in magPending) {
              var p = magPending[k], r = p.el._magRect;
              if (!r) continue;
              var mx = (p.x - (r.left + r.width / 2)) * 0.16;
              var my = (p.y - (r.top + r.height / 2)) * 0.16;
              p.el.style.transform = 'translate(' + mx.toFixed(1) + 'px,' + my.toFixed(1) + 'px)';
            }
            magPending = {};
          });
        });
        el.addEventListener('mouseleave', function () { el.style.transform = ''; el._magRect = null; });
      });
      // re-cache rects after layout settles (debounced resize) — avoids stale cached boxes
      var rzT = null;
      addEventListener('resize', function () {
        clearTimeout(rzT);
        rzT = setTimeout(function () {
          for (var i = 0; i < magEls.length; i++) if (magEls[i]._magRect) magEls[i]._magRect = null;
        }, 150);
      }, { passive: true });
    }

    /* ---------- 8) smooth anchor scroll with fixed-nav offset ---------- */
    var NAV_OFFSET = 80;
    document.addEventListener('click', function (e) {
      var a = e.target && e.target.closest ? e.target.closest('a[href^="#"]') : null;
      if (!a) return;
      var href = a.getAttribute('href');
      if (!href || href === '#') return;
      var id = decodeURIComponent(href.replace(/^#/, ''));
      if (!id) return;
      var target = document.getElementById(id);
      if (!target) return;
      e.preventDefault();
      var y = target.getBoundingClientRect().top
            + (window.pageYOffset || document.documentElement.scrollTop || 0)
            - NAV_OFFSET;
      window.scrollTo({ top: Math.max(0, y), behavior: reduced ? 'auto' : 'smooth' });
      if (history.pushState) history.pushState(null, '', '#' + id);
    }, false);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot, { once: true });
  } else {
    boot();
  }
})();
