/* Online Kutubxona + Admin Panel — theme toggle + animations
   Ulanish: <script src="{% static 'main/js/theme_toggle.js' %}" defer></script>
*/

(function () {
  'use strict';

  const root = document.documentElement;
  const storageKey = 'onlineKutubxonaTheme';
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;

  function getSavedTheme() {
    try {
      return localStorage.getItem(storageKey);
    } catch (error) {
      return null;
    }
  }

  function saveTheme(theme) {
    try {
      localStorage.setItem(storageKey, theme);
    } catch (error) {
      // localStorage yopiq bo'lsa ham sayt ishlashda davom etadi.
    }
  }

  function applyTheme(theme) {
    const isDark = theme === 'dark';
    root.classList.toggle('dark', isDark);
    root.setAttribute('data-theme', theme);

    const toggle = document.querySelector('[data-theme-toggle]');
    if (toggle) {
      toggle.setAttribute('aria-pressed', String(isDark));
      toggle.textContent = isDark ? '☀️ Kunduzgi rejim' : '🌙 Tungi rejim';
      toggle.title = isDark ? 'Kunduzgi rejimga o‘tish' : 'Tungi rejimga o‘tish';
    }
  }

  function addThemeToggle() {
    const nav = document.querySelector('nav');
    if (!nav || document.querySelector('[data-theme-toggle]')) return;

    const toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.className = 'js-theme-toggle';
    toggle.setAttribute('data-theme-toggle', '');
    toggle.setAttribute('aria-label', 'Kunduzgi yoki tungi rejimni almashtirish');

    toggle.addEventListener('click', function () {
      const nextTheme = root.classList.contains('dark') ? 'light' : 'dark';
      applyTheme(nextTheme);
      saveTheme(nextTheme);
    });

    nav.appendChild(toggle);
    applyTheme(root.classList.contains('dark') ? 'dark' : 'light');
  }

  function markCurrentNavLink() {
    const currentPath = window.location.pathname;
    document.querySelectorAll('nav a[href]').forEach(function (link) {
      try {
        const linkPath = new URL(link.href, window.location.origin).pathname;
        if (linkPath === currentPath) {
          link.setAttribute('aria-current', 'page');
          link.classList.add('is-active');
        }
      } catch (error) {
        // noto'g'ri href bo'lsa e'tiborsiz qoldiramiz
      }
    });
  }

  function wrapWideTables() {
    document.querySelectorAll('main table').forEach(function (table) {
      if (table.parentElement && table.parentElement.classList.contains('js-table-wrap')) return;

      const wrapper = document.createElement('div');
      wrapper.className = 'js-table-wrap';
      table.parentNode.insertBefore(wrapper, table);
      wrapper.appendChild(table);
    });
  }

  function revealOnScroll() {
    const revealItems = document.querySelectorAll('main > *, footer, nav');

    if (!('IntersectionObserver' in window)) {
      revealItems.forEach(function (item) {
        item.classList.add('is-visible');
      });
      return;
    }

    const observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08 });

    revealItems.forEach(function (item, index) {
      item.classList.add('js-reveal');
      item.style.transitionDelay = Math.min(index * 45, 360) + 'ms';
      observer.observe(item);
    });
  }

  const initialTheme = getSavedTheme() || (prefersDark ? 'dark' : 'light');
  applyTheme(initialTheme);

  document.addEventListener('DOMContentLoaded', function () {
    addThemeToggle();
    markCurrentNavLink();
    wrapWideTables();
    revealOnScroll();
  });
})();
