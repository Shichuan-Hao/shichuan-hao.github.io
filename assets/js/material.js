/* ============================================================
   资料页 — 隐藏右侧面板 & 内容区全宽
   ============================================================ */
(function () {
  'use strict';

  function onReady(fn) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', fn);
    } else {
      fn();
    }
  }

  onReady(function () {
    var panel = document.getElementById('panel-wrapper');
    if (panel) panel.style.display = 'none';

    var col = document.querySelector('#main .row > div:first-child');
    if (col) {
      col.classList.remove('col-xl-9');
      col.classList.add('col-xl-12');
    }
  });
})();
