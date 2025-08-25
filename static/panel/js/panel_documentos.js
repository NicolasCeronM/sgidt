/****************************************************
 * SGIDT - Gestión de Documentos (con toasts mejorados)
 ****************************************************/

const listUrl = "/app/documentos/api/list/";
const uploadUrl = "/app/documentos/api/upload/";

const tbody = document.getElementById("documentsTableBody");
const btnFilter = document.getElementById("btnFilter");
const dateFrom = document.getElementById("dateFrom");
const dateTo = document.getElementById("dateTo");
const docType = document.getElementById("docType");
const docStatus = document.getElementById("docStatus");

const uploadArea = document.getElementById("uploadArea");
const fileInput = document.getElementById("fileInput");
const btnSelect = document.getElementById("btnSelect");

// Contenedor de toasts
let toastContainer = document.getElementById("toastContainer");
if (!toastContainer) {
  toastContainer = document.createElement("div");
  toastContainer.id = "toastContainer";
  toastContainer.className = "toast-container";
  document.body.appendChild(toastContainer);
}

const activeToasts = new Map();
const MAX_TOASTS = 3;

function ensureMaxToasts() {
  while (toastContainer.children.length > MAX_TOASTS) {
    toastContainer.firstElementChild?.remove();
  }
}

function showToast(message, type = "info", opts = {}) {
  const { key, duration = 5000, persist = false } = opts;
  let toast = key ? activeToasts.get(key) : null;

  if (!toast) {
    toast = document.createElement("div");
    toast.className = `toast ${type}`;

    const textNode = document.createElement("span");
    textNode.className = "toast-text";
    textNode.textContent = message;
    toast.appendChild(textNode);

    const closeBtn = document.createElement("button");
    closeBtn.type = "button";
    closeBtn.className = "toast-close";
    closeBtn.textContent = "×";
    closeBtn.onclick = () => {
      toast.remove();
      if (key) activeToasts.delete(key);
    };
    toast.appendChild(closeBtn);

    toastContainer.appendChild(toast);
    ensureMaxToasts();
    if (key) activeToasts.set(key, toast);
  } else {
    toast.className = `toast ${type}`;
    toast.querySelector(".toast-text").textContent = message;
  }

  if (!persist) {
    if (toast._timeout) clearTimeout(toast._timeout);
    toast._timeout = setTimeout(() => {
      toast.remove();
      if (key) activeToasts.delete(key);
    }, duration);
  }
  return toast;
}

function getCookie(name) {
  const v = `; ${document.cookie}`.split(`; ${name}=`);
  if (v.length === 2) return v.pop().split(";").shift();
}
const csrftoken = getCookie("csrftoken");

btnSelect?.addEventListener("click", () => fileInput?.click());
uploadArea?.addEventListener("click", () => fileInput?.click());
uploadArea?.addEventListener("dragover", (e) => {
  e.preventDefault();
  uploadArea.classList.add("dragging");
});
uploadArea?.addEventListener("dragleave", () => {
  uploadArea.classList.remove("dragging");
});
uploadArea?.addEventListener("drop", (e) => {
  e.preventDefault();
  uploadArea.classList.remove("dragging");
  if (e.dataTransfer?.files?.length) doUpload(e.dataTransfer.files);
});
fileInput?.addEventListener("change", () => {
  if (fileInput.files?.length) doUpload(fileInput.files);
});

async function doUpload(files) {
  const allowedExt = [".pdf", ".jpg", ".jpeg", ".png"];
  const maxSize = 10 * 1024 * 1024;

  const fd = new FormData();
  for (const f of files) {
    const name = f.name.toLowerCase();
    if (allowedExt.some((ext) => name.endsWith(ext)) && f.size <= maxSize) {
      fd.append("files[]", f);
    }
  }
  if (![...fd.keys()].length) return;

  const UPLOAD_KEY = "upload-progress";
  const uploadingToast = showToast("Subiendo archivos…", "info", {
    key: UPLOAD_KEY,
    persist: true,
  });
  if (uploadingToast && !uploadingToast.querySelector(".spinner")) {
    const sp = document.createElement("div");
    sp.className = "spinner";
    uploadingToast.insertBefore(sp, uploadingToast.firstChild);
  }

  try {
    const res = await fetch(uploadUrl, {
      method: "POST",
      headers: { "X-CSRFToken": csrftoken },
      body: fd,
    });

    if (!res.ok) {
      const text = await res.text();
      showToast(`Error al subir: ${text}`, "error", {
        key: UPLOAD_KEY,
        duration: 6000,
      });
      return;
    }

    const data = await res.json();
    const normalizedErrors = (data.errors || []).map((e) =>
      /UNIQUE constraint.*hash_sha256/i.test(e)
        ? "Archivo duplicado en la empresa"
        : e
    );

    let msg = `Subidos: ${data.created}`;
    if (data.skipped) msg += ` | Duplicados: ${data.skipped}`;
    if (normalizedErrors.length)
      msg += ` | Errores: ${normalizedErrors.join(", ")}`;

    if (data.created > 0 && !normalizedErrors.length) {
      showToast(msg, "success", { key: UPLOAD_KEY, duration: 5000 });
    } else if (data.created > 0 && normalizedErrors.length) {
      showToast(msg, "warning", { key: UPLOAD_KEY, duration: 7000 });
    } else if (data.skipped && !data.created && !normalizedErrors.length) {
      showToast(msg, "warning", { key: UPLOAD_KEY, duration: 5000 });
    } else {
      showToast(msg, "error", { key: UPLOAD_KEY, duration: 8000 });
    }

    if (fileInput) fileInput.value = "";
    loadDocuments();
  } catch (err) {
    showToast(`Error de red al subir: ${String(err)}`, "error", {
      key: UPLOAD_KEY,
      duration: 7000,
    });
  }
}

btnFilter?.addEventListener("click", () => loadDocuments());

async function loadDocuments() {
  const params = new URLSearchParams();
  if (dateFrom?.value) params.set("dateFrom", dateFrom.value);
  if (dateTo?.value) params.set("dateTo", dateTo.value);
  if (docType?.value) params.set("docType", docType.value);
  if (docStatus?.value) params.set("docStatus", docStatus.value);

  try {
    const res = await fetch(`${listUrl}?${params.toString()}`, {
      headers: { Accept: "application/json" },
    });
    if (!res.ok) {
      tbody.innerHTML = `<tr><td colspan="7">Error al cargar documentos</td></tr>`;
      showToast("No se pudieron cargar los documentos.", "error");
      return;
    }
    const data = await res.json();
    renderRows(data.results || []);
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7">Error al cargar documentos</td></tr>`;
    showToast(`Error de red al listar: ${String(err)}`, "error");
  }
}

function renderRows(rows) {
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="7">No hay documentos</td></tr>`;
    return;
  }

  const fmtCLP = (v) =>
    new Intl.NumberFormat("es-CL", {
      style: "currency",
      currency: "CLP",
      maximumFractionDigits: 0,
    }).format(v);

  tbody.innerHTML = rows
    .map(
      (r) => `
    <tr>
      <td>${r.fecha || "—"}</td>
      <td>${r.tipo || "—"}</td>
      <td>${r.folio || "—"}</td>
      <td>${r.rut_emisor || "—"}</td>
      <td>${r.total == null ? "—" : fmtCLP(r.total)}</td>
      <td>${r.estado || "—"}</td>
      <td>${
        r.archivo
          ? `<a href="${r.archivo}" target="_blank" rel="noopener">Ver</a>`
          : ""
      }</td>
    </tr>
  `
    )
    .join("");
}

document.addEventListener("DOMContentLoaded", loadDocuments);
