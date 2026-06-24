(function () {
  var reloadScheduled = false;
  var RELOAD_KEY = "__macroRecoverAt";

  function shouldHandle(anchor, event) {
    if (!anchor || event.button !== 0) return false;
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return false;
    if (anchor.target && anchor.target !== "_self" && anchor.target !== "_top") return false;
    if (anchor.hasAttribute("download")) return false;

    var url = new URL(anchor.href, window.location.href);
    if (url.origin !== window.location.origin) return false;
    return url.pathname === "/app" || url.pathname.indexOf("/app/") === 0 || url.pathname.indexOf("/adminus") === 0;
  }

  function scheduleRecover() {
    if (reloadScheduled || document.visibilityState !== "visible") return;

    var last = Number(sessionStorage.getItem(RELOAD_KEY) || 0);
    if (Date.now() - last < 3000) return;

    reloadScheduled = true;
    sessionStorage.setItem(RELOAD_KEY, String(Date.now()));

    setTimeout(function () {
      var url = new URL(window.location.href);
      url.searchParams.set("_recover", String(Date.now()));
      window.location.replace(url.toString());
    }, 50);
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
    var requestUrl = "";
    try {
      requestUrl =
        typeof input === "string"
          ? input
          : input instanceof URL
            ? input.href
            : input && input.url
              ? input.url
              : "";
    } catch (_) {}

    var sameOrigin = false;
    try {
      sameOrigin = new URL(requestUrl, window.location.href).origin === window.location.origin;
    } catch (_) {}

    return nativeFetch(input, init).catch(function (err) {
      if (sameOrigin && navigator.onLine) scheduleRecover();
      throw err;
    });
  };

  window.__macroHardNavigation = "external";
  document.addEventListener("click", handleClick, true);
})();
