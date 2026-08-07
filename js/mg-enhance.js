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

  // ─── Typewriter ────────────────────────────────────────────────────
  function initTypewriter() {
    var el = document.getElementById('hero-typewriter');
    if (!el) return;
    var raw = el.getAttribute('data-words');
    if (!raw) return;
    var words = raw.split(',');
    var colors = ['#6fb5ff', '#3a9928', '#d11a1a'];
    var wordIdx = 0;
    var colorIdx = 0;
    var charIdx = words[0].length;
    var deleting = true;

    function tick() {
      var word = words[wordIdx];
      if (deleting) {
        charIdx--;
        el.textContent = word.slice(0, charIdx);
        if (charIdx === 0) {
          deleting = false;
          wordIdx = (wordIdx + 1) % words.length;
          colorIdx = (colorIdx + 1) % colors.length;
          el.style.color = colors[colorIdx];
          setTimeout(tick, 400);
          return;
        }
        setTimeout(tick, 60 + Math.random() * 40);
      } else {
        var target = words[wordIdx];
        charIdx++;
        el.textContent = target.slice(0, charIdx);
        if (charIdx === target.length) {
          deleting = true;
          el.classList.remove('typing');
          setTimeout(function() { el.classList.add('typing'); setTimeout(tick, 600); }, 2000);
          return;
        }
        setTimeout(tick, 90 + Math.random() * 50);
      }
    }
    setTimeout(function() { el.classList.add('typing'); setTimeout(tick, 600); }, 3000);
  }

  // ─── Mods filter ───────────────────────────────────────────────────
  function initModsFilter() {
    var grid = document.getElementById('mods-grid');
    if (!grid) return;
    var cards = grid.querySelectorAll('[data-category]');
    var buttons = document.querySelectorAll('#cat-filters .mods-filter__btn');
    var search = document.getElementById('search-input');
    var countEl = document.querySelector('.mods-filter__count');
    var total = cards.length;
    var activeCat = 'All';
    var query = '';

    function applyHash() {
      var hash = window.location.hash.slice(1);
      if (hash) { activeCat = hash; }
    }

    function filter() {
      var q = query.toLowerCase();
      var visible = 0;
      cards.forEach(function(card) {
        var cat = card.getAttribute('data-category');
        var title = (card.querySelector('.mod-card__title') || {}).textContent || '';
        var base = (card.querySelector('.mod-card__base-game') || {}).textContent || '';
        var matchCat = activeCat === 'All' || cat === activeCat;
        var matchSearch = !q || title.toLowerCase().indexOf(q) !== -1 || base.toLowerCase().indexOf(q) !== -1;
        var show = matchCat && matchSearch;
        card.style.display = show ? '' : 'none';
        if (show) visible++;
      });
      if (countEl) countEl.textContent = visible + ' OF ' + total + ' MODS';
      buttons.forEach(function(btn) {
        btn.classList.toggle('mods-filter__btn--active', btn.textContent === activeCat);
      });
    }

    buttons.forEach(function(btn) {
      btn.addEventListener('click', function() {
        activeCat = btn.textContent;
        filter();
      });
    });

    if (search) {
      search.addEventListener('input', function() {
        query = search.value;
        filter();
      });
    }

    applyHash();
    filter();
    window.addEventListener('hashchange', function() { applyHash(); filter(); });
  }

  // ─── News filter ──────────────────────────────────────────────────
  function initNewsFilter() {
    var grid = document.getElementById('posts-grid');
    if (!grid) return;
    var cards = grid.querySelectorAll('.news-grid-card');
    var featured = document.getElementById('news-featured');
    var searchInputs = document.querySelectorAll('#news-search, #news-mobile-search');
    var topicLinks = document.querySelectorAll('[data-topic]');
    var monthLinks = document.querySelectorAll('[data-month]');
    var resultsBar = document.getElementById('news-results-bar');
    var resultsText = document.getElementById('news-results-text');
    var resultsClear = document.getElementById('news-results-clear');
    var total = cards.length;
    var activeTopic = '';
    var activeMonth = '';
    var query = '';

    function filter() {
      var q = query.toLowerCase();
      var visible = 0;
      cards.forEach(function(card) {
        var tags = (card.getAttribute('data-tags') || '').split(',');
        var date = card.getAttribute('data-date') || '';
        var title = (card.querySelector('.news-grid-card__title') || {}).textContent || '';
        var excerpt = (card.querySelector('.news-grid-card__excerpt') || {}).textContent || '';
        var matchTopic = !activeTopic || tags.indexOf(activeTopic) !== -1;
        var matchMonth = !activeMonth || date === activeMonth;
        var matchSearch = !q || title.toLowerCase().indexOf(q) !== -1 || excerpt.toLowerCase().indexOf(q) !== -1;
        var show = matchTopic && matchMonth && matchSearch;
        card.style.display = show ? '' : 'none';
        if (show) visible++;
      });
      var filtering = activeTopic || activeMonth || query;
      if (featured) featured.style.display = filtering ? 'none' : '';
      if (resultsBar) {
        resultsBar.style.display = filtering ? '' : 'none';
        var label = activeTopic || activeMonth || query;
        if (resultsText) resultsText.textContent = 'Showing ' + visible + ' of ' + total + ' posts for ' + label;
      }
    }

    if (resultsClear) {
      resultsClear.addEventListener('click', function(e) {
        e.preventDefault();
        activeTopic = '';
        activeMonth = '';
        query = '';
        searchInputs.forEach(function(input) { input.value = ''; });
        filter();
      });
    }

    topicLinks.forEach(function(link) {
      link.addEventListener('click', function(e) {
        e.preventDefault();
        var t = link.getAttribute('data-topic');
        activeTopic = activeTopic === t ? '' : t;
        activeMonth = '';
        filter();
      });
    });

    monthLinks.forEach(function(link) {
      link.addEventListener('click', function(e) {
        e.preventDefault();
        var m = link.getAttribute('data-month');
        activeMonth = activeMonth === m ? '' : m;
        activeTopic = '';
        filter();
      });
    });

    searchInputs.forEach(function(input) {
      input.addEventListener('input', function() {
        query = input.value;
        searchInputs.forEach(function(other) { if (other !== input) other.value = query; });
        filter();
      });
    });
  }

  // ─── Submit form steps ────────────────────────────────────────────
  function initSubmitSteps() {
    var formSection = document.querySelector('.submit-form[data-action]');
    if (!formSection) return;
    var apiUrl = formSection.getAttribute('data-action');
    var formData = {};
    var currentStep = 1;

    function goStep(n) {
      currentStep = n;
      ['step-1','step-2','step-3','step-success'].forEach(function(id) {
        var el = document.getElementById(id);
        if (el) el.hidden = true;
      });
      var tabs = document.querySelectorAll('.step-tab');
      tabs.forEach(function(t) { t.classList.remove('step-tab--active'); t.classList.add('step-tab--inactive'); });
      document.querySelectorAll('.step-tab__num').forEach(function(s) { s.classList.remove('step-tab__num--active'); });

      if (n === 'success') {
        document.getElementById('step-success').hidden = false;
        document.querySelector('.submit-steps').style.display = 'none';
        return;
      }
      document.getElementById('step-' + n).hidden = false;
      var tab = document.getElementById('step-' + n + '-tab');
      if (tab) { tab.classList.add('step-tab--active'); tab.classList.remove('step-tab--inactive'); }
      var num = document.getElementById('s' + n + '-num');
      if (num) num.classList.add('step-tab__num--active');

      if (n === 3) buildPreview();
    }

    function buildPreview() {
      var p = document.getElementById('submit-preview');
      p.innerHTML = '';
      var eyebrow = document.createElement('div');
      eyebrow.className = 'submit-preview__eyebrow';
      eyebrow.textContent = 'YOUR SUBMISSION';
      p.appendChild(eyebrow);
      var rows = [['Title',formData.title||'—'],['Base game',formData.baseGame||'—'],['Category',formData.category||'—'],['Stats',formData.stats||'—'],['Designer',formData.designer||'—'],['Version',formData.version||'—']];
      rows.forEach(function(pair) {
        var row = document.createElement('div');
        row.className = 'submit-preview__row';
        var key = document.createElement('span');
        key.className = 'submit-preview__key';
        key.textContent = pair[0];
        var val = document.createElement('span');
        val.className = 'submit-preview__val';
        val.textContent = pair[1];
        row.appendChild(key);
        row.appendChild(val);
        p.appendChild(row);
      });
      if (formData.desc) {
        var desc = document.createElement('div');
        desc.className = 'submit-preview__desc';
        desc.textContent = formData.desc;
        p.appendChild(desc);
      }
    }

    formSection.querySelectorAll('.field-input, .field-file').forEach(function(input) {
      var key = input.getAttribute('data-key');
      if (!key) return;
      input.addEventListener('input', function() { formData[key] = input.value; });
    });

    formSection.querySelectorAll('.cat-btn').forEach(function(btn) {
      btn.addEventListener('click', function() {
        formData.category = btn.getAttribute('data-value');
        formSection.querySelectorAll('.cat-btn').forEach(function(b) {
          b.style.background = '';
          b.style.color = '';
          b.style.borderColor = '';
        });
        btn.style.background = '#0c4f8d';
        btn.style.color = '#fff';
        btn.style.borderColor = '#0c4f8d';
      });
    });

    formSection.querySelectorAll('.submit-next').forEach(function(btn) {
      btn.addEventListener('click', function() { goStep(parseInt(btn.getAttribute('data-target'))); });
    });
    formSection.querySelectorAll('.submit-back').forEach(function(btn) {
      btn.addEventListener('click', function() { goStep(parseInt(btn.getAttribute('data-target'))); });
    });

    var finalBtn = document.getElementById('submit-final');
    if (finalBtn) {
      finalBtn.addEventListener('click', function() {
        if (!document.getElementById('agree-check').checked) {
          alert('Please confirm the agreement first.');
          return;
        }
        if (!formData.email || formData.email.indexOf('@') === -1) {
          alert('Please provide a valid email address in step 2.');
          return;
        }
        finalBtn.disabled = true;
        finalBtn.textContent = 'Submitting...';
        fetch(apiUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData)
        }).then(function(r) {
          if (!r.ok) throw new Error('Failed');
          return r.json();
        }).then(function() {
          goStep('success');
        }).catch(function() {
          finalBtn.disabled = false;
          finalBtn.textContent = 'Submit mod';
          alert('Submission failed. Please check your connection and try again.');
        });
      });
    }
  }

  // ─── Subscribe form ───────────────────────────────────────────────
  function initSubscribeForm() {
    var form = document.getElementById('sub-form');
    if (!form) return;
    var emailInput = form.querySelector('.sub-form__email');
    var submitBtn = form.querySelector('.sub-form__submit');
    var errorEl = document.getElementById('sub-error');
    var success = document.getElementById('sub-success');
    if (!submitBtn || !emailInput) return;
    var apiUrl = submitBtn.getAttribute('data-action') || 'https://tools.moddable.games/api/subscribe';

    submitBtn.addEventListener('click', function() {
      var email = emailInput.value.trim();
      if (!email || email.indexOf('@') === -1) {
        emailInput.style.borderColor = '#d11a1a';
        emailInput.focus();
        return;
      }
      submitBtn.disabled = true;
      submitBtn.textContent = 'Subscribing...';
      fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email, source: 'subscribe-page' })
      }).then(function(r) {
        if (!r.ok) throw new Error('Failed');
        return r.json();
      }).then(function() {
        form.style.display = 'none';
        if (success) success.classList.add('sub-success--show');
      }).catch(function() {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Subscribe';
        emailInput.style.borderColor = '#d11a1a';
        if (errorEl) errorEl.hidden = false;
      });
    });
  }

  // ─── Copy buttons ─────────────────────────────────────────────────
  function initCopyButtons() {
    document.querySelectorAll('[data-copy]').forEach(function(btn) {
      btn.addEventListener('click', function() {
        var text = btn.getAttribute('data-copy');
        navigator.clipboard.writeText(text).then(function() {
          var copied = btn.nextElementSibling;
          if (copied) copied.style.display = 'inline';
          setTimeout(function() { if (copied) copied.style.display = ''; }, 2000);
        });
      });
    });
  }

  // ─── Init ──────────────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', function() {
    initReveal();
    initParallax();
    initHeroAnim();
    initTypewriter();
    initModsFilter();
    initNewsFilter();
    initSubmitSteps();
    initSubscribeForm();
    initCopyButtons();
  });
})();
