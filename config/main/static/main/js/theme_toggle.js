/* Online Kutubxona — theme toggle + light animations
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
      // Browser localStorage yopiq bo'lsa ham sayt ishlashda davom etadi.
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

  const initialTheme = getSavedTheme() || (prefersDark ? 'dark' : 'light');
  applyTheme(initialTheme);

  document.addEventListener('DOMContentLoaded', function () {
    const nav = document.querySelector('nav');

    if (nav && !document.querySelector('[data-theme-toggle]')) {
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

    const revealItems = document.querySelectorAll('main > *, footer, nav');

    if ('IntersectionObserver' in window) {
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
    } else {
      revealItems.forEach(function (item) {
        item.classList.add('is-visible');
      });
    }
  });
})();
