(function() {
  var css = document.createElement('style');
  css.textContent = [
    '.splash-overlay{',
    '  position:fixed;inset:0;z-index:99999;',
    '  background:linear-gradient(160deg,#0f172a 0%,#1e293b 60%,#334155 100%);',
    '  display:flex;align-items:center;justify-content:center;',
    '  cursor:pointer;-webkit-tap-highlight-color:transparent;',
    '  transition:transform .6s cubic-bezier(.4,0,.2,1),opacity .6s ease;',
    '}',
    '.splash-overlay.dismiss{',
    '  transform:translateY(-100%);opacity:0;pointer-events:none;',
    '}',
    '.splash-content{text-align:center;color:#fff;animation:splashFadeIn .8s ease}',
    '.splash-avatar{',
    '  width:88px;height:88px;margin:0 auto 24px;border-radius:50%;overflow:hidden;',
    '  border:3px solid rgba(255,255,255,.2);',
    '  box-shadow:0 0 40px rgba(59,130,246,.2)',
    '}',
    '.splash-avatar img{width:100%;height:100%;object-fit:cover}',
    '.splash-title{font-size:2.2rem;font-weight:700;letter-spacing:4px;margin-bottom:10px}',
    '.splash-subtitle{font-size:1rem;color:rgba(255,255,255,.55);font-weight:300;letter-spacing:2px}',
    '.splash-hint{margin-top:48px;display:flex;flex-direction:column;align-items:center;gap:8px;color:rgba(255,255,255,.35);font-size:.85rem;letter-spacing:1px}',
    '.splash-arrow{display:inline-block;width:20px;height:20px;border-right:2px solid rgba(255,255,255,.4);border-top:2px solid rgba(255,255,255,.4);transform:rotate(-45deg);animation:splashBounce 1.6s ease infinite}',
    '#main-wrapper{visibility:hidden}',
    '.splash-overlay.dismiss + #main-wrapper{visibility:visible}',
    '@keyframes splashFadeIn{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}',
    '@keyframes splashBounce{0%,100%{transform:rotate(-45deg) translateY(0);opacity:.3}50%{transform:rotate(-45deg) translateY(-6px);opacity:1}}'
  ].join('\n');
  document.head.appendChild(css);

  function init() {
    var div = document.createElement('div');
    div.id = 'splash';
    div.className = 'splash-overlay';
    div.innerHTML =
      '<div class="splash-content">' +
        '<div class="splash-avatar"><img src="/assets/img/avatar/avatar.png" alt="avatar" onerror="this.style.display=\'none\'"></div>' +
        '<h1 class="splash-title">字节漫步</h1>' +
        '<p class="splash-subtitle">探索技术的无限可能</p>' +
        '<div class="splash-hint"><span>点击或上滑进入</span><i class="splash-arrow"></i></div>' +
      '</div>';

    document.body.insertBefore(div, document.body.firstChild);

    var dismissed = false;
    var startY = 0;

    function dismiss() {
      if (dismissed) return;
      dismissed = true;
      div.classList.add('dismiss');
      var main = document.getElementById('main-wrapper');
      if (main) main.style.visibility = 'visible';
      div.addEventListener('transitionend', function() { div.remove(); }, { once: true });
    }

    div.addEventListener('click', dismiss);
    div.addEventListener('touchstart', function(e) { startY = e.touches[0].clientY; }, { passive: true });
    div.addEventListener('touchmove', function(e) { if (startY - e.touches[0].clientY > 40) dismiss(); }, { passive: true });
    div.addEventListener('wheel', function(e) { if (e.deltaY < 0) dismiss(); }, { passive: true });
  }

  if (document.body) {
    init();
  } else {
    document.addEventListener('DOMContentLoaded', init);
  }
})();
