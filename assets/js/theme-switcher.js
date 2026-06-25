/**
 * Theme Switcher — Chirpy 默认 ↔ GitHub Primer
 * 使用 localStorage 持久化，初始跟随上次选择
 */
(function () {
  'use strict';

  const THEME_KEY = 'site-theme';
  const THEME_GITHUB = 'github';

  function getStoredTheme() {
    try {
      return localStorage.getItem(THEME_KEY);
    } catch (e) {
      return null;
    }
  }

  function setStoredTheme(theme) {
    try {
      if (theme) localStorage.setItem(THEME_KEY, theme);
      else localStorage.removeItem(THEME_KEY);
    } catch (e) { /* ignore */ }
  }

  function applyTheme(theme) {
    if (theme === THEME_GITHUB) {
      document.documentElement.setAttribute('data-theme', THEME_GITHUB);
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
    updateToggleUI(theme);
  }

  function updateToggleUI(activeTheme) {
    var btn = document.getElementById('theme-toggle');
    if (!btn) return;
    if (activeTheme === THEME_GITHUB) {
      btn.classList.add('active');
      btn.title = '当前：GitHub 风格 · 点击切换 Chirpy 默认';
    } else {
      btn.classList.remove('active');
      btn.title = '当前：Chirpy 默认 · 点击切换 GitHub 风格';
    }
  }

  function toggleTheme() {
    var current = document.documentElement.getAttribute('data-theme');
    var next = (current === THEME_GITHUB) ? null : THEME_GITHUB;
    setStoredTheme(next);
    applyTheme(next);
  }

  // --- 立即应用主题（防闪烁） ---
  var stored = getStoredTheme();
  applyTheme(stored);

  // --- 按钮事件（等 DOM 就绪） ---
  function bindEvents() {
    var btn = document.getElementById('theme-toggle');
    if (btn) {
      btn.addEventListener('click', toggleTheme);
    }

    // 键盘快捷键：Ctrl+Shift+T
    document.addEventListener('keydown', function (e) {
      if (e.ctrlKey && e.shiftKey && e.key === 'T') {
        e.preventDefault();
        toggleTheme();
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bindEvents);
  } else {
    bindEvents();
  }
})();
