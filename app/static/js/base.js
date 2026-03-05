// base.js — helpers UI (Municunco)
// - Sidebar: off-canvas (móvil/tablet) + colapsable (desktop)
// - Toasts
// - Modal preview
// - Dropzone
// - Confirm modal

(function () {
  "use strict";

  // =========================
  // Sidebar (off-canvas en móvil/tablet + colapsable en desktop)
  // =========================
  function initSidebar() {
    const toggleBtn = document.querySelector("[data-sidebar-toggle]");
    const sidebar = document.querySelector("#sidebar");
    const closeBtns = document.querySelectorAll("[data-sidebar-close]");

    if (!toggleBtn || !sidebar) return;

    const isDesktop = () => window.matchMedia("(min-width: 1025px)").matches;

    const setMobileOpen = (open) => {
      document.body.classList.toggle("sidebar-open", open);
      toggleBtn.setAttribute("aria-expanded", open ? "true" : "false");
      document.body.style.overflow = open ? "hidden" : "";
    };

    const toggleDesktopCollapse = () => {
      const collapsed = document.body.classList.toggle("sidebar-collapsed");
      // en desktop no bloqueamos scroll
      toggleBtn.setAttribute("aria-expanded", collapsed ? "false" : "true");
    };

    toggleBtn.addEventListener("click", () => {
      if (isDesktop()) {
        toggleDesktopCollapse();
        return;
      }
      const open = document.body.classList.contains("sidebar-open");
      setMobileOpen(!open);
    });

    closeBtns.forEach((b) =>
      b.addEventListener("click", () => {
        if (!isDesktop()) setMobileOpen(false);
      })
    );

    // ESC cierra menú móvil
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && document.body.classList.contains("sidebar-open")) {
        setMobileOpen(false);
      }
    });

    // Si pasas a desktop, aseguramos estado móvil limpio (sin backdrop)
    const mq = window.matchMedia("(min-width: 1025px)");
    const onChange = () => {
      if (mq.matches) {
        setMobileOpen(false);
      } else {
        // al volver a móvil, si estaba colapsado, lo dejamos visible
        document.body.classList.remove("sidebar-collapsed");
        toggleBtn.setAttribute("aria-expanded", "false");
      }
    };
    if (mq.addEventListener) mq.addEventListener("change", onChange);
    else mq.addListener(onChange);
  }

  // =========================
  // Toasts
  // =========================
  function initToasts() {
    const removeToast = (toast) => {
      if (!toast || !toast.isConnected) return;

      toast.style.opacity = "0";
      toast.style.transform = "translateY(-6px)";
      toast.style.transition = "opacity .18s ease, transform .18s ease";
      window.setTimeout(() => {
        if (toast.isConnected) toast.remove();
      }, 220);
    };

    document.addEventListener("click", (e) => {
      const btn = e.target.closest(".toast__close,[data-toast-close]");
      if (!btn) return;

      const toast = btn.closest(".toast,[data-toast]");
      if (!toast) return;

      removeToast(toast);
    });

    document.querySelectorAll(".toast,[data-toast]").forEach((toast) => {
      window.setTimeout(() => removeToast(toast), 4500);
    });
  }

  // =========================
  // Modal preview (resizable + tamaños)
  // =========================
  function initModalPreview() {
    const modal = document.querySelector("#previewModal");
    if (!modal) return;

    const panel = modal.querySelector(".modal__panel");
    const head = modal.querySelector(".modal__head");
    const titleEl = modal.querySelector(".modal__title");
    const frame = modal.querySelector("iframe");

    if (!panel || !head || !frame) return;

    const KEY = "municunco_preview_size";
    const SIZES = ["sm", "md", "lg", "xl"];

    const getSavedSize = () => {
      try {
        return localStorage.getItem(KEY) || "md";
      } catch (_) {
        return "md";
      }
    };

    const applySize = (size) => {
      const s = SIZES.includes(size) ? size : "md";

      panel.style.width = "";
      panel.style.height = "";

      SIZES.forEach((x) => panel.classList.remove(`is-${x}`));
      panel.classList.add(`is-${s}`);

      try {
        localStorage.setItem(KEY, s);
      } catch (_) {}

      head.querySelectorAll("[data-preview-size]").forEach((b) => {
        const pressed = b.getAttribute("data-preview-size") === s ? "true" : "false";
        b.setAttribute("aria-pressed", pressed);
      });
    };

    if (!head.querySelector(".modal__tools")) {
      const tools = document.createElement("div");
      tools.className = "modal__tools";
      tools.innerHTML = `
        <button class="iconbtn" type="button" data-preview-size="sm" aria-pressed="false" aria-label="Vista previa: tamaño chico">−</button>
        <button class="iconbtn" type="button" data-preview-size="md" aria-pressed="false" aria-label="Vista previa: tamaño normal">1:1</button>
        <button class="iconbtn" type="button" data-preview-size="lg" aria-pressed="false" aria-label="Vista previa: tamaño grande">+</button>
        <button class="iconbtn" type="button" data-preview-size="xl" aria-pressed="false" aria-label="Vista previa: pantalla completa">⛶</button>
      `;
      const closeBtn = head.querySelector("[data-modal-close]");
      head.insertBefore(tools, closeBtn);
    }

    const open = (url, title) => {
      modal.classList.add("is-open");
      modal.setAttribute("aria-hidden", "false");

      if (titleEl) titleEl.textContent = title || "Vista previa";
      frame.src = url || "about:blank";

      applySize(getSavedSize());
    };

    const close = () => {
      modal.classList.remove("is-open");
      modal.setAttribute("aria-hidden", "true");
      frame.src = "about:blank";
    };

    document.addEventListener("click", (e) => {
      const openBtn = e.target.closest("[data-modal-open]");
      if (openBtn) {
        const url = openBtn.getAttribute("data-modal-open");
        const title = openBtn.getAttribute("data-modal-title") || "Vista previa";
        open(url, title);
        return;
      }

      const sizeBtn = e.target.closest("[data-preview-size]");
      if (sizeBtn && modal.classList.contains("is-open")) {
        applySize(sizeBtn.getAttribute("data-preview-size"));
        return;
      }

      const closeBtn = e.target.closest("[data-modal-close]");
      if (closeBtn) {
        close();
        return;
      }

      if (e.target === modal) close();
    });

    document.addEventListener("keydown", (e) => {
      if (!modal.classList.contains("is-open")) return;

      if (e.key === "Escape") close();

      if (e.key === "+" || e.key === "=") {
        const cur = getSavedSize();
        const idx = Math.min(SIZES.indexOf(cur) + 1, SIZES.length - 1);
        applySize(SIZES[idx]);
      }

      if (e.key === "-") {
        const cur = getSavedSize();
        const idx = Math.max(SIZES.indexOf(cur) - 1, 0);
        applySize(SIZES[idx]);
      }
    });
  }

  // =========================
  // Dropzone
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

      try {
        const dt = new DataTransfer();
        for (const f of files) dt.items.add(f);
        input.files = dt.files;
      } catch (_) {}

      updateCount();
    });

    input.addEventListener("change", updateCount);
    updateCount();
  }

  // =========================
  // Confirm modal
  // =========================
  function initConfirmModal() {
    const modal = document.querySelector("#confirmModal");
    if (!modal) return;

    const titleEl = modal.querySelector("[data-confirm-title]");
    const textEl = modal.querySelector("[data-confirm-text]");
    const okBtn = modal.querySelector("[data-confirm-ok]");
    const cancelBtn = modal.querySelectorAll("[data-confirm-cancel]");

    let pendingForm = null;

    const open = (opts) => {
      if (titleEl) titleEl.textContent = opts.title || "Confirmar acción";
      if (textEl) textEl.textContent = opts.message || "¿Confirmas esta acción?";
      if (okBtn) okBtn.textContent = opts.okText || "Confirmar";
      modal.classList.add("is-open");
      modal.setAttribute("aria-hidden", "false");
    };

    const close = () => {
      modal.classList.remove("is-open");
      modal.setAttribute("aria-hidden", "true");
      pendingForm = null;
    };

    document.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-confirm]");
      if (!btn) return;

      e.preventDefault();
      pendingForm = btn.closest("form");

      open({
        title: btn.getAttribute("data-confirm-title") || "Confirmación",
        message: btn.getAttribute("data-confirm") || "¿Confirmas esta acción?",
        okText: btn.getAttribute("data-confirm-ok") || "Confirmar",
      });
    });

    cancelBtn.forEach((b) => b.addEventListener("click", close));

    if (okBtn) {
      okBtn.addEventListener("click", () => {
        if (pendingForm) pendingForm.submit();
        close();
      });
    }

    modal.addEventListener("click", (e) => {
      if (e.target === modal) close();
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && modal.classList.contains("is-open")) close();
    });
  }

  // =========================
  // Init
  // =========================
  window.addEventListener("DOMContentLoaded", () => {
    initSidebar();
    initToasts();
    initModalPreview();
    initDropzone();
    initConfirmModal();
  });
})();