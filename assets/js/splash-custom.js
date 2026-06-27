/**
 * splash-custom.js
 * 对 Chirpy 原版 splash.js 的扩展，不侵入原文件。
 *
 * 功能：
 *   1. 只在首次访问时显示着陆页（localStorage 持久记录）
 *   2. 之后任何访问（刷新/关闭重开）都直接跳过
 *   3. 着陆页内容从 _includes/splash.html 模板读取，方便编辑
 *
 * 维护方式：
 *   - 升级 Chirpy 主题时直接覆盖 splash.js
 *   - 自定义逻辑和模板内容保持在本文件 + splash.html 中
 */
(function() {
  var SPLASH_KEY = '_splash_shown';

  // 已显示过 → 直接跳过
  if (localStorage.getItem(SPLASH_KEY)) {
    skipSplashOnLoad();
    return;
  }

  // 首次访问 → 渲染着陆页
  whenReady(function() {
    showFromTemplate();
  });

  // --- 功能函数 ---

  /* 尽早跳过 splash：等待 #splash 创建后立即移除 */
  function skipSplashOnLoad() {
    function trySkip(retries) {
      var splash = document.getElementById('splash');
      if (splash) {
        splash.style.display = 'none';
        splash.remove();
        var main = document.getElementById('main-wrapper');
        if (main) main.style.visibility = 'visible';
      } else if (retries > 0) {
        setTimeout(function() { trySkip(retries - 1); }, 15);
      }
    }
    whenReady(function() { trySkip(30); });
  }

  function whenReady(fn) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', fn);
    } else {
      fn();
    }
  }

  /* 从 splash.html 模板读取内容，替换原版 splash.js 创建的 overlay */
  function showFromTemplate() {
    function tryApply(retries) {
      var existingSplash = document.getElementById('splash');
      var tpl = document.getElementById('splash-tpl');

      if (!existingSplash || !tpl) {
        if (retries > 0) setTimeout(function() { tryApply(retries - 1); }, 20);
        return;
      }

      applyTemplate(existingSplash, tpl);
    }

    setTimeout(function() { tryApply(20); }, 0);
  }

  function applyTemplate(splashEl, tpl) {
    var wrapper = document.createElement('div');
    wrapper.innerHTML = tpl.innerHTML;

    var styleEl = wrapper.querySelector('style');
    var splashContent = wrapper.querySelector('#splash');
    if (!splashContent) return;

    if (styleEl) {
      var newStyle = document.createElement('style');
      newStyle.textContent = styleEl.textContent;
      document.head.appendChild(newStyle);
    }

    splashEl.className = splashContent.className;
    splashEl.innerHTML = splashContent.innerHTML;

    // 首次关闭时记录到 localStorage，之后永不再显示
    function markShown() {
      localStorage.setItem(SPLASH_KEY, '1');
    }
    splashEl.addEventListener('click', markShown, { once: true, capture: true });
    splashEl.addEventListener('wheel', markShown, { once: true, capture: true });
    splashEl.addEventListener('touchmove', markShown, { once: true, capture: true });
  }
})();
