// base.js — UI helpers (Municunco)
// - Toasts (cerrar + autocerrar)
// - Modal preview
// - Dropzone
// - Confirm modal PRO
// Nota: el menú activo lo marca el servidor (Jinja) para evitar duplicados.

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
      const ms = 4500;
      window.setTimeout(() => removeToast(toast), ms);
    });
  }

  // =========================
  // Modal preview
  // =========================
  function initModalPreview() {
    const modal = document.querySelector("#previewModal");
    if (!modal) return;

    const titleEl = modal.querySelector(".modal__title");
    const frame = modal.querySelector("iframe");

    const open = (url, title) => {
      modal.classList.add("is-open");
      modal.setAttribute("aria-hidden", "false");
      if (titleEl) titleEl.textContent = title || "Vista previa";
      if (frame) frame.src = url || "about:blank";
    };

    const close = () => {
      modal.classList.remove("is-open");
      modal.setAttribute("aria-hidden", "true");
      if (frame) frame.src = "about:blank";
    };

    document.addEventListener("click", (e) => {
      const openBtn = e.target.closest("[data-modal-open]");
      if (openBtn) {
        const url = openBtn.getAttribute("data-modal-open");
        const title = openBtn.getAttribute("data-modal-title") || "Vista previa";
        open(url, title);
        return;
      }

      const closeBtn = e.target.closest("[data-modal-close]");
      if (closeBtn) {
        close();
        return;
      }

      // Clic fuera (backdrop)
      if (e.target === modal) close();
    });

    // ESC
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && modal.classList.contains("is-open")) close();
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

      // Intento seguro: DataTransfer (mejor compatibilidad)
      try {
        const dt = new DataTransfer();
        for (const f of files) dt.items.add(f);
        input.files = dt.files;
      } catch (_) {
        // Si el navegador no lo permite, igual actualizamos contador (no romper)
      }

      updateCount();
    });

    input.addEventListener("change", updateCount);
    updateCount();
  }

  // =========================
  // Confirm modal PRO
  // =========================
  function initConfirmModal() {
    const modal = document.querySelector("#confirmModal");
    if (!modal) return;

    const titleEl = modal.querySelector("[data-confirm-title]");
    const textEl = modal.querySelector("[data-confirm-text]"); // ✅ coincide con tu HTML
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