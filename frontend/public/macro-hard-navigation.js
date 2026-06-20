(function () {
  function shouldHandle(anchor, event) {
    if (!anchor || event.button !== 0) return false;
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return false;
    if (anchor.target && anchor.target !== "_self" && anchor.target !== "_top") return false;
    if (anchor.hasAttribute("download")) return false;

    var url = new URL(anchor.href, window.location.href);
    if (url.origin !== window.location.origin) return false;
    return url.pathname === "/app" || url.pathname.indexOf("/app/") === 0 || url.pathname.indexOf("/adminus") === 0;
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

  window.__macroHardNavigation = "external";
  window.addEventListener("click", handleClick, true);
  document.addEventListener("click", handleClick, true);
})();
