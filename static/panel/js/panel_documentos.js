/****************************************************
 * SGIDT - Gestión de Documentos (UI mejorada)
 * - Línea de carga superior (page progress)
 * - Dropzone drag & drop (clase .dragging)
 * - Toasts (reutiliza tus estilos)
 ****************************************************/

const listUrl = "/app/documentos/api/list/";
const uploadUrl = "/app/documentos/api/upload/";

// ---- DOM ----
const tbody = document.getElementById("documentsTableBody");
const btnFilter = document.getElementById("btnFilter");
const dateFrom = document.getElementById("dateFrom");
const dateTo = document.getElementById("dateTo");
const docType = document.getElementById("docType");
const docStatus = document.getElementById("docStatus");

const uploadArea = document.getElementById("uploadArea");
let fileInput = document.getElementById("fileInput");
const fileInputShadow = document.getElementById("fileInputShadow"); // si existe
const btnSelect = document.getElementById("btnSelect");

// usar shadow si existe
if (fileInputShadow) fileInput = fileInputShadow;

// ---- Línea de carga (tipo NProgress minimal) ----
const pageProgress = document.getElementById("pageProgress");
let progressTimer = null;

function progressStart() {
  if (!pageProgress) return;
  pageProgress.style.transform = "scaleX(0.05)";
  pageProgress.style.opacity = "1";
  clearInterval(progressTimer);
  progressTimer = setInterval(() => {
    const current = parseFloat(pageProgress.dataset.p || "0.05");
    const next = Math.min(current + Math.random() * 0.08, 0.9);
    pageProgress.style.transform = `scaleX(${next})`;
    pageProgress.dataset.p = String(next);
  }, 250);
}
function progressSet(p) {
  if (!pageProgress) return;
  pageProgress.style.transform = `scaleX(${p})`;
  pageProgress.dataset.p = String(p);
}
function progressDone() {
  if (!pageProgress) return;
  clearInterval(progressTimer);
  progressSet(1);
  setTimeout(() => {
    pageProgress.style.opacity = "0";
    pageProgress.dataset.p = "0";
    pageProgress.style.transform = "scaleX(0)";
  }, 220);
}

// ---- Toasts (compatibles con tu implementación previa) ----
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
    const t = document.createElement("span");
    t.className = "toast-text";
    t.textContent = message;
    toast.appendChild(t);
    const close = document.createElement("button");
    close.type = "button";
    close.className = "toast-close";
    close.textContent = "×";
    close.onclick = () => { toast.remove(); if (key) activeToasts.delete(key); };
    toast.appendChild(close);
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
      toast.remove(); if (key) activeToasts.delete(key);
    }, duration);
  }
  return toast;
}

// ---- CSRF ----
function getCookie(name) {
  const v = `; ${document.cookie}`.split(`; ${name}=`);
  if (v.length === 2) return v.pop().split(";").shift();
}
const csrftoken = getCookie("csrftoken");

// ---- Upload interactions ----
btnSelect?.addEventListener("click", () => fileInput?.click());
uploadArea?.addEventListener("click", (e) => {
  if (e.target.closest("button")) return;
  fileInput?.click();
});
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
      addQueueItem(f); // pinta en la cola con barra
    }
  }
  if (![...fd.keys()].length) return;

  const UPLOAD_KEY = "upload-progress";
  const uploadingToast = showToast("Subiendo archivos…", "info", { key: UPLOAD_KEY, persist: true });
  if (uploadingToast && !uploadingToast.querySelector(".spinner")) {
    const sp = document.createElement("div");
    sp.className = "spinner";
    uploadingToast.insertBefore(sp, uploadingToast.firstChild);
  }

  progressStart();
  try {
    const res = await fetch(uploadUrl, {
      method: "POST",
      headers: { "X-CSRFToken": csrftoken },
      body: fd,
    });

    if (!res.ok) {
      const text = await res.text();
      showToast(`Error al subir: ${text}`, "error", { key: UPLOAD_KEY, duration: 6000 });
      progressDone();
      return;
    }

    const data = await res.json();
    const normalizedErrors = (data.errors || []).map((e) =>
      /UNIQUE constraint.*hash_sha256/i.test(e) ? "Archivo duplicado en la empresa" : e
    );

    let msg = `Subidos: ${data.created || 0}`;
    if (data.skipped) msg += ` | Duplicados: ${data.skipped}`;
    if (normalizedErrors.length) msg += ` | Errores: ${normalizedErrors.join(", ")}`;

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
    await loadDocuments();
  } catch (err) {
    showToast(`Error de red al subir: ${String(err)}`, "error", { key: UPLOAD_KEY, duration: 7000 });
  } finally {
    progressDone();
    // marca todas las barras como completas
    document.querySelectorAll(".q-item .bar").forEach(b => (b.style.width = "100%"));
  }
}

// pinta item en cola con barra de progreso “simulada”
function addQueueItem(file) {
  const q = document.getElementById("queue");
  if (!q) return;
  q.hidden = false;
  const li = document.createElement("li");
  li.className = "q-item";
  li.innerHTML = `
    <div class="q-file">
      <i class="fas fa-file"></i>
      <div class="q-meta">
        <strong class="name">${file.name}</strong>
        <small class="size">${(file.size / 1024 / 1024).toFixed(2)} MB</small>
      </div>
    </div>
    <div class="q-progress">
      <div class="bar"></div>
      <span class="pct">0%</span>
    </div>`;
  q.appendChild(li);

  // animación simple (client-side). El “done real” lo hace progressDone()
  let p = 0;
  const id = setInterval(() => {
    p = Math.min(p + 8, 92);
    li.querySelector(".bar").style.width = p + "%";
    li.querySelector(".pct").textContent = p + "%";
    if (p >= 92) clearInterval(id);
  }, 120);
}

// ---- Listado / filtros ----
btnFilter?.addEventListener("click", () => loadDocuments());
document.addEventListener("DOMContentLoaded", () => loadDocuments());

async function loadDocuments() {
  const params = new URLSearchParams();
  if (dateFrom?.value) params.set("dateFrom", dateFrom.value);
  if (dateTo?.value) params.set("dateTo", dateTo.value);
  if (docType?.value) params.set("docType", docType.value);
  if (docStatus?.value) params.set("docStatus", docStatus.value);

  const empty = document.getElementById("tbl-empty");
  try {
    const res = await fetch(`${listUrl}?${params.toString()}`, {
      headers: { Accept: "application/json" },
    });
    if (!res.ok) throw new Error("Respuesta inválida");

    const data = await res.json();
    const rows = data.results || [];

    // Toggle del estado vacío (y render de filas)
    if (!rows.length) {
      tbody.innerHTML = "";       // limpiamos la tabla
      if (empty) empty.hidden = false; // mostramos "Aún no hay documentos"
    } else {
      if (empty) empty.hidden = true;  // ocultamos el empty-state
      renderRows(rows);
    }

    // (Opcional) contador de resultados si usas #result-info
    const info = document.getElementById("result-info");
    if (info) info.textContent = rows.length ? `${rows.length} resultados` : "Sin resultados";

  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7">Error al cargar documentos</td></tr>`;
    const msg = err?.message || String(err);
    showToast(`No se pudieron cargar los documentos: ${msg}`, "error");
    const empty = document.getElementById("tbl-empty");
    if (empty) empty.hidden = true;
  }
}

function renderRows(rows) {
  const fmtCLP = (v) =>
    new Intl.NumberFormat("es-CL", { style: "currency", currency: "CLP", maximumFractionDigits: 0 })
      .format(v);

  tbody.innerHTML = rows.map((r) => `
    <tr>
      <td>${r.fecha || "—"}</td>
      <td>${r.tipo || "—"}</td>
      <td>${r.folio || "—"}</td>
      <td>${r.rut_emisor || "—"}</td>
      <td class="num">${r.total == null ? "—" : fmtCLP(r.total)}</td>
      <td>${r.estado || "—"}</td>
      <td>${r.archivo ? `<a href="${r.archivo}" target="_blank" rel="noopener">Ver</a>` : ""}</td>
    </tr>
  `).join("");
}

function renderRows(rows) {
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="7">No hay documentos</td></tr>`;
    return;
  }
  const fmtCLP = (v) =>
    new Intl.NumberFormat("es-CL", { style: "currency", currency: "CLP", maximumFractionDigits: 0 }).format(v);

  tbody.innerHTML = rows
    .map((r) => `
      <tr>
        <td>${r.fecha || "—"}</td>
        <td>${r.tipo || "—"}</td>
        <td>${r.folio || "—"}</td>
        <td>${r.rut_emisor || "—"}</td>
        <td class="num">${r.total == null ? "—" : fmtCLP(r.total)}</td>
        <td>
          <span class="badge ${
            r.estado === "procesado" || r.estado === "validado"
              ? "badge-success"
              : r.estado === "cola" || r.estado === "pendiente"
              ? "badge-warning"
              : "badge-error"
          }">${r.estado || "—"}</span>
        </td>
        <td class="actions">
          ${r.archivo ? `<a class="act" href="${r.archivo}" target="_blank" rel="noopener">Ver</a>` : ""}
          <a class="act" href="#">Detalle</a>
        </td>
      </tr>
    `)
    .join("");
}
