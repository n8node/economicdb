(function () {
  var FETCH_TIMEOUT_MS = 12000;
  var BANNER_ID = "macro-network-banner";

  function shouldHandle(anchor, event) {
    if (!anchor || event.button !== 0) return false;
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return false;
    if (anchor.target && anchor.target !== "_self" && anchor.target !== "_top") return false;
    if (anchor.hasAttribute("download")) return false;

    var url = new URL(anchor.href, window.location.href);
    if (url.origin !== window.location.origin) return false;
    return url.pathname === "/app" || url.pathname.indexOf("/app/") === 0 || url.pathname.indexOf("/adminus") === 0;
  }

  function requestUrl(input) {
    try {
      if (typeof input === "string") return input;
      if (input instanceof URL) return input.href;
      if (input && input.url) return input.url;
    } catch (_) {}
    return "";
  }

  function isSameOrigin(input) {
    try {
      return new URL(requestUrl(input), window.location.href).origin === window.location.origin;
    } catch (_) {
      return false;
    }
  }

  function showBanner() {
    window.dispatchEvent(new CustomEvent("macro:network-stale", { detail: { reason: "fetch" } }));
    if (document.getElementById(BANNER_ID)) return;

    var wrap = document.createElement("div");
    wrap.id = BANNER_ID;
    wrap.setAttribute("role", "alert");
    wrap.style.cssText =
      "position:fixed;inset:0;z-index:99999;display:flex;align-items:center;justify-content:center;padding:24px;background:rgba(20,24,31,.55);";

    var card = document.createElement("div");
    card.style.cssText =
      "width:min(420px,100%);padding:24px;border-radius:14px;background:#fff;border:1px solid #e4e7ec;box-shadow:0 16px 48px rgba(20,24,31,.18);font-family:Inter,sans-serif;";

    var title = document.createElement("p");
    title.textContent = "Соединение прервано";
    title.style.cssText = "margin:0 0 8px;font-size:18px;font-weight:600;color:#14181f;";

    var hint = document.createElement("p");
    hint.textContent =
      "Запрос к серверу не завершился. Нажмите кнопку — на Windows это надёжнее, чем ждать автоматического восстановления.";
    hint.style.cssText = "margin:0 0 16px;line-height:1.5;color:#5b6271;font-size:14px;";

    var btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = "Перезагрузить";
    btn.style.cssText =
      "width:100%;padding:10px 16px;border:0;border-radius:10px;background:#1b7561;color:#fff;font-size:14px;font-weight:600;cursor:pointer;";
    btn.onclick = function () {
      window.location.href = "/app?_fresh=" + Date.now();
    };

    card.appendChild(title);
    card.appendChild(hint);
    card.appendChild(btn);
    wrap.appendChild(card);
    document.body.appendChild(wrap);
  }

  function handleClick(event) {
    var target = event.target;
    if (!target || !target.closest) return;

    var anchor = target.closest("a[href]");
    if (!shouldHandle(anchor, event)) return;

    event.preventDefault();
    if (event.stopImmediatePropagation) event.stopImmediatePropagation();
    window.location.assign(anchor.href);
  }

  var nativeFetch = window.fetch.bind(window);
  window.fetch = function (input, init) {
    init = init || {};
    if (init.signal) {
      return nativeFetch(input, init).catch(function (err) {
        if (isSameOrigin(input)) showBanner();
        throw err;
      });
    }

    var controller = new AbortController();
    var timeoutId = window.setTimeout(function () {
      controller.abort();
    }, FETCH_TIMEOUT_MS);

    var nextInit = {};
    for (var key in init) {
      if (Object.prototype.hasOwnProperty.call(init, key)) nextInit[key] = init[key];
    }
    nextInit.signal = controller.signal;

    return nativeFetch(input, nextInit)
      .then(function (response) {
        window.clearTimeout(timeoutId);
        return response;
      })
      .catch(function (err) {
        window.clearTimeout(timeoutId);
        if (isSameOrigin(input)) showBanner();
        throw err;
      });
  };

  window.__macroHardNavigation = "external";
  document.addEventListener("click", handleClick, true);
})();
