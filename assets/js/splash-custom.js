/**
 * splash-custom.js
 * 对 Chirpy 原版 splash.js 的扩展，不侵入原文件。
 *
 * 功能：
 *   1. 同会话内页面切换不重复显示着陆页（sessionStorage）
 *   2. 页面刷新时正常显示着陆页
 *   3. 着陆页内容从 _includes/splash.html 模板读取，方便编辑
 *
 * 维护方式：
 *   - 升级 Chirpy 主题时直接覆盖 splash.js
 *   - 自定义逻辑和模板内容保持在本文件 + splash.html 中
 */
(function() {
  var SPLASH_KEY = '_splash_entered';

  // --- 工具 ---

  function isRefresh() {
    try {
      var nav = performance.getEntriesByType('navigation')[0];
      return nav && nav.type === 'reload';
    } catch (e) { return false; }
  }

  // --- 主逻辑 ---

  // 刷新时清除标记，确保着陆页重新出现
  if (isRefresh()) {
    sessionStorage.removeItem(SPLASH_KEY);
  }

  // 同会话内二次导航 → 跳过着陆页
  if (!isRefresh() && sessionStorage.getItem(SPLASH_KEY)) {
    whenReady(function() {
      skipSplash();
    });
    return;
  }

  // 首次访问 / 刷新后 → 从模板渲染着陆页
  whenReady(function() {
    showFromTemplate();
  });

  // --- 功能函数 ---

  /* 等待 splash.js 创建 #splash 后执行回调 */
  function whenReady(fn) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', fn);
    } else {
      fn();
    }
  }

  /* 跳过 splash：移除 overlay，显示主内容 */
  function skipSplash() {
    var splash = document.getElementById('splash');
    if (splash) { splash.style.display = 'none'; splash.remove(); }
    var main = document.getElementById('main-wrapper');
    if (main) main.style.visibility = 'visible';
  }

  /* 从 splash.html 模板读取内容，替换原版 splash.js 创建的 overlay */
  function showFromTemplate() {
    // 等待 splash.js 和模板都就绪
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
    // 解析模板
    var wrapper = document.createElement('div');
    wrapper.innerHTML = tpl.innerHTML;

    // 提取模板中的 style 和 splash 内容
    var styleEl = wrapper.querySelector('style');
    var splashContent = wrapper.querySelector('#splash');
    if (!splashContent) return;

    // 注入模板的 CSS（追加在 splash.js 的 style 之后，同优先级下后者覆盖前者）
    if (styleEl) {
      var newStyle = document.createElement('style');
      newStyle.textContent = styleEl.textContent;
      document.head.appendChild(newStyle);
    }

    // 用模板内容替换 splash.js 创建的 overlay 内部
    splashEl.className = splashContent.className;
    splashEl.innerHTML = splashContent.innerHTML;

    // 拦截关闭事件，写入 sessionStorage
    function markEntered() {
      sessionStorage.setItem(SPLASH_KEY, '1');
    }
    // capture 阶段先于 splash.js 的冒泡处理器执行
    splashEl.addEventListener('click', markEntered, { once: true, capture: true });
    splashEl.addEventListener('wheel', markEntered, { once: true, capture: true });
    splashEl.addEventListener('touchmove', markEntered, { once: true, capture: true });
  }
})();
