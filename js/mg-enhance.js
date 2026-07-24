(function() {
  'use strict';

  // ─── Hamburger menu ─────────────────────────────────────────────────
  var hamburger = document.querySelector('.mg-navbar__hamburger');
  var drawer = document.querySelector('.mg-navbar__drawer');
  if (hamburger && drawer) {
    hamburger.addEventListener('click', function() {
      var open = drawer.classList.toggle('mg-navbar__drawer--open');
      hamburger.textContent = open ? '✕' : '☰';
      hamburger.setAttribute('aria-expanded', String(open));
    });
    drawer.addEventListener('click', function(e) {
      if (e.target.tagName === 'A') {
        drawer.classList.remove('mg-navbar__drawer--open');
        hamburger.textContent = '☰';
        hamburger.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // ─── Dropdown hover (desktop) ───────────────────────────────────────
  var navItems = document.querySelectorAll('.mg-navbar__item');
  navItems.forEach(function(item) {
    var dd = item.querySelector('.mg-navbar__dropdown');
    if (!dd) return;
    item.addEventListener('mouseenter', function() {
      dd.classList.add('mg-navbar__dropdown--visible');
    });
    item.addEventListener('mouseleave', function() {
      dd.classList.remove('mg-navbar__dropdown--visible');
    });
  });

  // ─── Scroll-reveal ──────────────────────────────────────────────────
  function initReveal() {
    var els = document.querySelectorAll('[data-reveal]');
    if (!els.length) return;

    var observer = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('revealed');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

    els.forEach(function(el, i) {
      el.style.setProperty('--stagger-index', i);
      observer.observe(el);
    });
  }

  // ─── Hero parallax ─────────────────────────────────────────────────
  function initParallax() {
    var hero = document.querySelector('.mg-hero');
    if (!hero) return;

    var hexLayer = hero.querySelector('.mg-hero__hex');
    var floatsLayer = hero.querySelector('.mg-hero__floats');
    var content = hero.querySelector('.mg-hero__content');
    var ticking = false;

    function onScroll() {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(function() {
        var rect = hero.getBoundingClientRect();
        var visible = rect.bottom > 0 && rect.top < window.innerHeight;
        if (visible) {
          var scrolled = Math.max(0, -rect.top);
          var ratio = Math.min(1, scrolled / (rect.height * 0.4));
          if (hexLayer) {
            hexLayer.style.transform = 'translateY(' + (ratio * 300) + 'px) scale(' + (1 + ratio * 0.35) + ') rotate(' + (ratio * 6) + 'deg)';
            hexLayer.style.opacity = (0.6 + ratio * 0.4).toFixed(2);
          }
          if (floatsLayer) {
            floatsLayer.style.transform = 'translateY(' + (ratio * -120) + 'px) scale(' + (1 + ratio * 0.4) + ')';
            floatsLayer.style.opacity = Math.max(0, 1 - ratio * 2.5).toFixed(2);
          }
          if (content) {
            content.style.transform = 'translateY(' + (ratio * -150) + 'px)';
            content.style.opacity = Math.max(0, 1 - ratio * 3).toFixed(2);
          }
        }
        ticking = false;
      });
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  // ─── Hero entry animation ──────────────────────────────────────────
  function initHeroAnim() {
    var anim = document.querySelector('.hero-anim');
    if (anim) {
      requestAnimationFrame(function() { anim.classList.add('hero-anim--in'); });
    }
  }

  // ─── Init ──────────────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', function() {
    initReveal();
    initParallax();
    initHeroAnim();
  });
})();
