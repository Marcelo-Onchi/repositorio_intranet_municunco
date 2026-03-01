/* base.js — UI básico (KISS)
   - Marca nav item activo según URL
   - Cierra alerts al click (opcional)
*/
(function () {
  "use strict";

  function normalizePath(path) {
    try {
      // Quita trailing slash excepto root
      if (path.length > 1 && path.endsWith("/")) return path.slice(0, -1);
      return path;
    } catch (_) {
      return path || "/";
    }
  }

  function markActiveNav() {
    const links = document.querySelectorAll(".nav__item[href]");
    if (!links.length) return;

    const current = normalizePath(window.location.pathname || "/");

    // Match exact primero, luego match por prefijo (para subrutas)
    let best = null;
    for (const a of links) {
      const href = a.getAttribute("href");
      if (!href || href === "#") continue;

      const target = normalizePath(href);

      if (target === current) {
        best = a;
        break;
      }

      // prefijo: /documents coincide con /documents/upload, etc.
      if (current.startsWith(target) && target !== "/") {
        if (!best) best = a;
        else if (target.length > normalizePath(best.getAttribute("href") || "").length) best = a;
      }
    }

    if (best) best.classList.add("is-active");
  }

  function makeAlertsDismissable() {
    // Si no quieres cerrar alerts al click, borra esta función.
    const alerts = document.querySelectorAll(".alert");
    for (const a of alerts) {
      a.style.cursor = "pointer";
      a.title = "Click para cerrar";
      a.addEventListener("click", () => {
        a.style.opacity = "0";
        a.style.transform = "translateY(-2px)";
        a.style.transition = "opacity .15s ease, transform .15s ease";
        setTimeout(() => a.remove(), 160);
      });
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    markActiveNav();
    makeAlertsDismissable();
  });
})();