// base.js — helpers UI (Municunco)
// - Toasts (cerrar + autocerrar)
// - Modal preview (tamaños + resize + atajos)
// - Dropzone
// - Confirm modal

(function () {
  "use strict";

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

    // Inserta la toolbar una sola vez (sin tocar HTML)
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

    // Atajos: ESC cierra, + agranda, - achica
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
      } catch (_) {
        // Navegadores restrictivos: no romper UX.
      }

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
    initToasts();
    initModalPreview();
    initDropzone();
    initConfirmModal();
  });
})();