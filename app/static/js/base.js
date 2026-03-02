// base.js — UI helpers (Municunco)
// - Menú activo (fallback si el server no lo marcó)
// - Toasts (cerrar + autocerrar)
// - Modal preview
// - Dropzone (si existe)

(function () {
  "use strict";

  // =========================
  // Menú activo automático
  // =========================
  function setActiveNav() {
    const navItems = Array.from(document.querySelectorAll(".nav__item[href]"));
    if (navItems.length === 0) return;

    // Si el server (Jinja) ya marcó alguno, no tocamos nada.
    const alreadyActive = navItems.some((a) => a.classList.contains("is-active"));
    if (alreadyActive) return;

    const current = window.location.pathname;

    // Buscar el match más específico (href más largo)
    let best = null;
    let bestLen = -1;

    for (const a of navItems) {
      const href = a.getAttribute("href");
      if (!href) continue;

      // No marcar logout ni anchors
      if (href.includes("logout") || href.startsWith("#")) continue;

      // Normalizar: sin trailing slash (excepto root)
      const cleanHref = href !== "/" ? href.replace(/\/+$/, "") : "/";
      const cleanCurrent = current !== "/" ? current.replace(/\/+$/, "") : "/";

      const isRoot = cleanHref === "/";
      const match = isRoot
        ? cleanCurrent === "/"
        : cleanCurrent === cleanHref || cleanCurrent.startsWith(cleanHref + "/");

      if (!match) continue;

      if (cleanHref.length > bestLen) {
        best = a;
        bestLen = cleanHref.length;
      }
    }

    if (best) best.classList.add("is-active");
  }

  // =========================
  // Toasts: cerrar + autocerrar
  // =========================
  function initToasts() {
    document.addEventListener("click", (e) => {
      const btn = e.target.closest(".toast__close,[data-toast-close]");
      if (!btn) return;

      const toast = btn.closest(".toast,[data-toast]");
      if (!toast) return;

      toast.style.opacity = "0";
      toast.style.transform = "translateY(-6px)";
      toast.style.transition = "opacity .18s ease, transform .18s ease";
      window.setTimeout(() => toast.remove(), 220);
    });

    document.querySelectorAll(".toast,[data-toast]").forEach((toast) => {
      const ms = 4500;

      window.setTimeout(() => {
        if (!toast.isConnected) return;

        toast.style.opacity = "0";
        toast.style.transform = "translateY(-6px)";
        toast.style.transition = "opacity .18s ease, transform .18s ease";
        window.setTimeout(() => toast.remove(), 220);
      }, ms);
    });
  }

  // =========================
  // Modal preview (delegado)
  // =========================
  function initModalPreview() {
    document.addEventListener("click", (e) => {
      const openBtn = e.target.closest("[data-modal-open]");
      if (openBtn) {
        const url = openBtn.getAttribute("data-modal-open");
        const title = openBtn.getAttribute("data-modal-title") || "Vista previa";
        const modal = document.querySelector("#previewModal");
        if (!modal) return;

        modal.classList.add("is-open");
        const t = modal.querySelector(".modal__title");
        const frame = modal.querySelector("iframe");
        if (t) t.textContent = title;
        if (frame) frame.src = url || "about:blank";
        return;
      }

      const closeBtn = e.target.closest("[data-modal-close]");
      if (closeBtn) {
        const modal = closeBtn.closest(".modal");
        if (!modal) return;

        modal.classList.remove("is-open");
        const frame = modal.querySelector("iframe");
        if (frame) frame.src = "about:blank";
        return;
      }

      // click fuera del panel
      if (e.target && e.target.classList && e.target.classList.contains("modal")) {
        const modal = e.target;
        modal.classList.remove("is-open");
        const frame = modal.querySelector("iframe");
        if (frame) frame.src = "about:blank";
      }
    });
  }

  // =========================
  // Dropzone (si existe)
  // =========================
  function initDropzone() {
    const dz = document.querySelector("[data-dropzone]");
    const input = document.querySelector("[data-file-input]");
    const counter = document.querySelector("[data-file-count]");

    if (!dz || !input) return;

    const updateCount = () => {
      if (!counter) return;
      const n = input.files ? input.files.length : 0;
      counter.textContent = n === 1 ? "1 archivo" : `${n} archivos`;
    };

    dz.addEventListener("click", () => input.click());

    dz.addEventListener("dragover", (ev) => {
      ev.preventDefault();
      dz.classList.add("is-dragover");
    });

    dz.addEventListener("dragleave", () => dz.classList.remove("is-dragover"));

    dz.addEventListener("drop", (ev) => {
      ev.preventDefault();
      dz.classList.remove("is-dragover");

      const files = ev.dataTransfer && ev.dataTransfer.files ? ev.dataTransfer.files : null;
      if (!files || files.length === 0) return;

      // En Chrome/Edge normalmente funciona asignar input.files
      try {
        input.files = files;
      } catch (_) {
        // Si no se puede asignar, no rompemos nada.
      }

      updateCount();
    });

    input.addEventListener("change", updateCount);
    updateCount();
  }

  // =========================
  // Init
  // =========================
  window.addEventListener("DOMContentLoaded", () => {
    setActiveNav();
    initToasts();
    initModalPreview();
    initDropzone();
  });
})();