// =========================
// Menú activo automático
// =========================
window.addEventListener("DOMContentLoaded", () => {
  const current = window.location.pathname;

  document.querySelectorAll(".nav__item[href]").forEach((a) => {
    const href = a.getAttribute("href");
    if (!href) return;
    if (href !== "/" && current.startsWith(href)) {
      a.classList.add("is-active");
    }
  });
});

// =========================
// Toasts: cerrar + autocerrar
// =========================
document.addEventListener("click", (e) => {
  const btn = e.target.closest(".toast__close");
  if (!btn) return;
  const toast = btn.closest(".toast");
  if (toast) toast.remove();
});

window.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".toast").forEach((toast) => {
    const ms = 4500;
    window.setTimeout(() => {
      if (!toast.isConnected) return;
      toast.style.opacity = "0";
      toast.style.transform = "translateY(-6px)";
      toast.style.transition = "opacity .18s ease, transform .18s ease";
      window.setTimeout(() => toast.remove(), 220);
    }, ms);
  });
});

// =========================
// Modal preview (delegado)
// =========================
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
    if (frame) frame.src = url;
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
  const modalBg = e.target.classList && e.target.classList.contains("modal");
  if (modalBg) {
    const modal = e.target;
    modal.classList.remove("is-open");
    const frame = modal.querySelector("iframe");
    if (frame) frame.src = "about:blank";
  }
});

// =========================
// Dropzone (si existe)
// =========================
window.addEventListener("DOMContentLoaded", () => {
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
    const files = ev.dataTransfer.files;
    if (!files || files.length === 0) return;

    // Asignar a input (compatibilidad)
    input.files = files;
    updateCount();
  });

  input.addEventListener("change", updateCount);
  updateCount();
});