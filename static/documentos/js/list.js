// static/documentos/js/list.js
import { listUrl, csrftoken } from "./api.js";
import { showToast } from "./ui.js";

const tbody = () => document.getElementById("documentsTableBody");

// cache simple por id para reutilizar los datos ya listados
const docCache = new Map();

// refs del modal
const $overlay = () => document.getElementById("docDetailOverlay");
const $content = () => document.getElementById("docDetailContent");
const $closeBtn = () => document.getElementById("docDetailClose");
const $viewBtn = () => document.getElementById("docViewBtn");
const $dlBtn = () => document.getElementById("docDownloadBtn");
const $pillE = () => document.getElementById("docEstadoPill");
const $pillSII = () => document.getElementById("docSiiPill");

// builders para acciones SII
const validarSiiUrl = (id) => `/api/v1/documentos/${id}/validar-sii/`;
const estadoSiiUrl = (id) => `/api/v1/documentos/${id}/estado-sii/`;

// --- UTILIDAD DEBOUNCE (Retraso inteligente) ---
function debounce(func, wait) {
  let timeout;
  return function(...args) {
    const context = this;
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(context, args), wait);
  };
}

export function wireFilters() {
  // Referencias a los inputs
  const searchInput = document.getElementById("filterSearch");
  const dateFromInput = document.getElementById("filterDateFrom");
  const dateToInput = document.getElementById("filterDateTo");
  const typeInput = document.getElementById("filterType");
  const statusInput = document.getElementById("filterStatus");
  const resetBtn = document.getElementById("btnResetFilters");

  // 1. Función de recarga con debounce (para texto)
  // Espera 400ms después de dejar de escribir para recargar
  const debouncedLoad = debounce(() => loadDocuments(), 400);

  // 2. Eventos para Búsqueda de Texto (Tiempo real)
  if (searchInput) {
    searchInput.addEventListener("input", debouncedLoad);
  }

  // 3. Eventos para Selectores y Fechas (Cambio inmediato pero suave)
  // Usamos debouncedLoad también aquí para unificar la experiencia fluida
  [dateFromInput, dateToInput, typeInput, statusInput].forEach(el => {
    if (el) el.addEventListener("change", debouncedLoad);
  });

  // 4. Botón Limpiar Filtros
  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      if (searchInput) searchInput.value = "";
      if (dateFromInput) dateFromInput.value = "";
      if (dateToInput) dateToInput.value = "";
      if (typeInput) typeInput.value = "";
      if (statusInput) statusInput.value = "";
      
      // Recargar inmediatamente
      loadDocuments();
    });
  }

  // 5. Carga inicial + retorno de historial
  function bootLoad() {
    try {
      loadDocuments();
    } catch (_) {}
  }
  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", bootLoad, { once: true });
  else bootLoad();
  
  window.addEventListener("pageshow", bootLoad);
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") bootLoad();
  });
  document.addEventListener("docs:reload", loadDocuments);

  // 6. Clicks en la tabla (Acciones y Modal)
  document
    .getElementById("documentsTable")
    ?.addEventListener("click", async (e) => {
      const act = e.target?.closest?.(".act");
      
      // Si es un botón de acción
      if (act) {
        e.preventDefault();
        e.stopPropagation();
        const id = act.dataset.id || act.closest("tr")?.getAttribute("data-doc-id");
        if (!id) return;
        
        if (act.classList.contains("act-validate")) return onValidateSii(id);
        if (act.classList.contains("act-refresh")) return onRefreshSii(id);
        if (act.classList.contains("act-open")) {
            // Para ver/descargar dejamos que el navegador maneje el link si tiene href,
            // o implementamos lógica custom si fuera necesario.
            if (act.getAttribute('href') && act.getAttribute('href') !== '#') {
                window.open(act.getAttribute('href'), '_blank');
            }
            return; 
        }
        return;
      }
      
      // Si es click en la fila (abrir modal)
      const tr = e.target.closest("tr[data-doc-id]");
      if (tr) {
        const id = tr.getAttribute("data-doc-id");
        openDetailModal(id);
      }
    });

  // 7. Auto-refresh suave si hay documentos validando
  setInterval(() => {
    const anyProcessing = !!document.querySelector("#documentsTable .badge--info");
    if (anyProcessing) document.dispatchEvent(new Event("docs:reload"));
  }, 10000);
}

export async function loadDocuments() {
  // Obtener valores de los filtros
  const search = document.getElementById("filterSearch")?.value || "";
  const dateFrom = document.getElementById("filterDateFrom")?.value || "";
  const dateTo = document.getElementById("filterDateTo")?.value || "";
  const docType = document.getElementById("filterType")?.value || "";
  const docStatus = document.getElementById("filterStatus")?.value || "";

  // Construir parámetros URL
  const params = new URLSearchParams();
  if (search) params.set("search", search);
  if (dateFrom) params.set("dateFrom", dateFrom);
  if (dateTo) params.set("dateTo", dateTo);
  if (docType) params.set("docType", docType);
  if (docStatus) params.set("docStatus", docStatus);

  // --- UI: Estado de Carga ---
  const tb = tbody();
  const empty = document.getElementById("tbl-empty");
  const skeleton = document.getElementById("tbl-skeleton");

  if (tb) tb.innerHTML = "";
  if (empty) empty.hidden = true;
  if (skeleton) skeleton.hidden = false;

  try {
    const res = await fetch(`${listUrl}?${params.toString()}`, {
      headers: { Accept: "application/json" },
      credentials: "include",
    });

    // Ocultar skeleton al recibir respuesta
    if (skeleton) skeleton.hidden = true;

    if (!res.ok) {
      throw new Error(`Respuesta inválida (${res.status})`);
    }

    const { results = [] } = await res.json();

    // Refrescar cache local
    docCache.clear();
    results.forEach((r) => {
      if (r?.id != null) docCache.set(String(r.id), r);
    });

    // --- UI: Renderizar Resultados ---
    if (!results.length) {
      // Sin resultados
      if (tb) tb.innerHTML = "";
      if (empty) {
          empty.hidden = false;
          empty.style.display = ''; // Asegurar display block/grid
      }
    } else {
      // Con resultados
      if (empty) {
          empty.hidden = true;
          empty.style.display = 'none'; 
      }
      renderRows(results);
    }

    // Actualizar texto de conteo
    const info = document.getElementById("result-info");
    if (info) {
        if (results.length === 0) info.textContent = "Sin resultados";
        else if (results.length === 1) info.textContent = "1 resultado";
        else info.textContent = `${results.length} resultados`;
    }

  } catch (e) {
    console.error("Error al cargar documentos:", e);
    if (skeleton) skeleton.hidden = true;
    if (empty) empty.hidden = true;
    
    // Mostrar mensaje de error en la tabla
    if (tb) tb.innerHTML = `
      <tr>
        <td colspan="9" class="empty-text">
          <i class="fas fa-exclamation-triangle" style="color: #ef4444;"></i>
          Error al cargar documentos.
        </td>
      </tr>`;
  }
}

function renderSiiBadge(r) {
  const est = (r.sii_estado || "").toUpperCase();
  if (!est) return "—";
  if (est === "EN_PROCESO" || est === "RECIBIDO") {
    return `<span class="badge badge--info">
      <i class="fa-solid fa-circle-notch fa-spin" style="margin-right:6px"></i>
      validando…
    </span>`;
  }
  if (est === "ACEPTADO") return `<span class="badge badge--success">aceptado</span>`;
  if (est === "RECHAZADO")
    return `<span class="badge badge--danger">rechazado</span>`;
  return escapeHtml(est.toLowerCase());
}

function renderRows(rows){
  const fmtCLP = (n) => (n==null ? "—" :
    new Intl.NumberFormat("es-CL", { style:"currency", currency:"CLP", maximumFractionDigits:0 }).format(n));

  const html = rows.map(r => `
    <tr data-doc-id="${r.id}">
      <td>${escapeHtml(r.fecha_emision || r.fecha || "—")}</td>
      <td>${escapeHtml(r.tipo_documento || r.tipo || "—")}</td>
      <td>${escapeHtml(r.folio ?? "—")}</td>
      <td>${escapeHtml(r.rut_proveedor || r.rut_emisor || "—")}</td>
      <td>${escapeHtml(r.razon_social_proveedor || r.razon_social || "—")}</td>
      <td class="num">${fmtCLP(r.total)}</td>
      <td>
        ${r.estado ? `<span class="badge ${r.estado==="procesado"||r.estado==="validado" ? "badge-success" :
                      (["cola","pendiente","procesando"].includes(r.estado) ? "badge--info" : "badge-error")}">${escapeHtml(r.estado)}</span>` : "—"}
      </td>
      <td>${renderSiiBadge(r)}</td>
      <td class="actions">
        ${ r.archivo ? `<a class="act act-open" href="${r.archivo}" target="_blank" rel="noopener" title="Ver"><i class="fa-solid fa-eye"></i></a>` : "" }
        ${ r.archivo ? `<a class="act act-open" href="${r.archivo}" download title="Descargar"><i class="fa-solid fa-download"></i></a>` : "" }

        <a class="act act-validate" href="#" data-id="${r.id}" title="Validar en SII" aria-label="Validar en SII">
          <i class="fa-solid fa-shield-alt"></i> </a>

        ${ r.sii_track_id ? `
          <a class="act act-refresh" href="#" data-id="${r.id}" title="Actualizar estado SII" aria-label="Actualizar estado SII">
            <i class="fa-solid fa-rotate"></i>
          </a>` : `
          <span class="act disabled" title="Valida primero para obtener Track ID" aria-label="Sin Track ID">
            <i class="fa-solid fa-rotate"></i>
          </span>`
        }
      </td>
    </tr>
  `).join("");

  tbody().innerHTML = html;
}

// =================================================================
// LÓGICA DEL MODAL DE DETALLE
// =================================================================

const fmtMoney = (n) =>
  n == null
    ? "—"
    : new Intl.NumberFormat("es-CL", {
        style: "currency",
        currency: "CLP",
        maximumFractionDigits: 0,
      }).format(n);

const fmtNumber = (n) =>
  n == null ? "—" : new Intl.NumberFormat("es-CL").format(n);

// Mapa de etiquetas
const LABELS = {
  tipo_documento: ["Tipo de Documento", "principal"],
  folio: ["Folio", "principal"],
  rut_proveedor: ["RUT Proveedor", "principal"],
  nombre_proveedor: ["Razón Social", "principal"],
  rut_emisor: ["RUT Proveedor", "principal"], 
  razon_social: ["Razón Social", "principal"], 

  fecha_emision: ["Fecha Emisión", "fechas"],
  fecha_vencimiento: ["Fecha Vencimiento", "fechas"],
  fecha_recepcion: ["Fecha Recepción", "fechas"],
  fecha: ["Fecha Emisión", "fechas"], 
  created_at: ["Fecha Creación", "fechas"],

  monto_neto: ["Neto", "montos"],
  neto: ["Neto", "montos"], 
  monto_exento: ["Exento", "montos"],
  exento: ["Exento", "montos"], 
  iva: ["IVA", "montos"],
  total: ["Total", "montos"],

  factura_afecta: ["Factura Afecta", "detalle"],
  descripcion: ["Descripción", "detalle"],
  tasa_iva: ["Tasa IVA", "detalle"],
  direccion: ["Dirección", "detalle"],
  comuna: ["Comuna", "detalle"],

  id: ["ID Interno", "meta"],
  nombre_archivo: ["Nombre Archivo", "meta"],
  origen: ["Origen de Carga", "meta"],
};

function isMoneyKey(key) {
  return ["monto_neto", "neto", "monto_exento", "exento", "iva", "total"].includes(key);
}

function openDetailModal(docId) {
  const doc = docCache.get(String(docId));
  if (!doc) {
    console.error("No se encontró el documento en caché:", docId);
    return;
  }

  // Mostrar skeleton en modal mientras carga detalle completo (si falta)
  $content().innerHTML = `
    <div class="kv-skel">
      <div class="skeleton"></div><div class="skeleton"></div>
      <div class="skeleton"></div><div class="skeleton"></div>
      <div class="skeleton"></div><div class="skeleton"></div>
    </div>`;

  paintDetail(doc, false);

  $overlay().style.display = "flex";
  $overlay().setAttribute("aria-hidden", "false");

  fetchDetailIfNeeded(docId);
}

function closeDetailModal() {
  $overlay().style.display = "none";
  $overlay().setAttribute("aria-hidden", "true");
}
$closeBtn()?.addEventListener("click", closeDetailModal);
$overlay()?.addEventListener("click", (e) => {
  if (e.target === $overlay()) closeDetailModal();
});

async function fetchDetailIfNeeded(id) {
  const cached = docCache.get(String(id));
  // Si ya tenemos datos detallados (ej: nombre_archivo), no volvemos a pedir
  if (cached && cached.nombre_archivo) {
    return;
  }
  
  try {
    const res = await fetch(`${listUrl}${id}/`, {
      headers: { Accept: "application/json" },
      credentials: "include",
    });
    if (res.ok) {
      const full = await res.json();
      const merged = { ...(cached || {}), ...(full || {}) };
      docCache.set(String(id), merged);
      paintDetail(merged, true); // true = es un refresco
    }
  } catch (_) { }
}

function paintDetail(doc, isRefresh = false) {
  const modalHtml = buildModalContent(doc);
  $content().innerHTML = modalHtml;

  if (isRefresh) return;

  // Pills
  if (doc.estado) {
    const kind =
      doc.estado === "procesado" || doc.estado === "validado"
        ? "ok"
        : ["cola", "pendiente", "procesando"].includes(doc.estado)
        ? "warn"
        : "err";
    setPill($pillE(), `Estado: ${doc.estado}`, kind);
  } else setPill($pillE(), "", "");

  if ("validado_sii" in doc || "sii_estado" in doc) {
    const est = (doc.sii_estado || "").toUpperCase();
    if (est === "ACEPTADO") setPill($pillSII(), "SII: aceptado", "ok");
    else if (est === "RECHAZADO") setPill($pillSII(), "SII: rechazado", "err");
    else if (est === "EN_PROCESO" || est === "RECIBIDO")
      setPill($pillSII(), "SII: validando…", "warn");
    else
      setPill(
        $pillSII(),
        doc.validado_sii ? doc.sii_estado || "SII OK" : "No validado SII",
        doc.validado_sii ? "ok" : "warn"
      );
  } else setPill($pillSII(), "", "");

  // Botones
  if (doc.archivo) {
    $viewBtn().href = doc.archivo;
    $viewBtn().hidden = false;
    $dlBtn().href = doc.archivo;
    $dlBtn().hidden = false;
  } else {
    $viewBtn().hidden = true;
    $dlBtn().hidden = true;
  }
}

function buildModalContent(data) {
  const groups = {
    principal: [],
    fechas: [],
    montos: [],
    detalle: [],
    meta: [],
    otros: [], 
  };

  const knownKeys = new Set([
      'estado', 'sii_estado', 'sii_track_id', 'validado_sii', 'archivo',
  ]);

  for (const [key, value] of Object.entries(data)) {
    if (value === null || value === "" || knownKeys.has(key)) continue;

    const [label, group] = LABELS[key] || [key, 'otros'];

    const finalLabel =
      group === "otros"
        ? key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())
        : label;

    groups[group].push({
      key: finalLabel,
      value: formatValue(value, key),
    });
  }

  let html = "";
  const tipoDoc = data.tipo_documento || data.tipo || "Documento";
  const folio = data.folio || data.id;
  html += `<h3 id="docDetailTitle" class="detail-section-title">${tipoDoc} #${folio}</h3>`;

  const groupOrder = [
    { id: "principal", title: "Información Principal" },
    { id: "montos", title: "Montos" },
    { id: "fechas", title: "Fechas" },
    { id: "detalle", title: "Detalles Adicionales" },
    { id: "meta", title: "Metadata" },
    { id: "otros", title: "Otros Datos" },
  ];

  for (const group of groupOrder) {
    const items = groups[group.id];
    // Deduplicar items por clave visual
    const uniqueItems = Array.from(new Map(items.map(item => [item.key, item])).values());
    
    if (uniqueItems.length > 0) {
      if (group.id !== "principal") {
        html += `<h4 class="detail-section-title">${group.title}</h4>`;
      }

      html += '<div class="detail-section">';
      for (const item of uniqueItems) {
        html += `
          <div class="kv-pair">
            <span class="kv-key">${item.key}</span>
            <span class="kv-value">${item.value}</span>
          </div>
        `;
      }
      html += "</div>";
    }
  }

  return html;
}

/* =======================
    Acciones SII (Fetch)
   ======================= */
async function onValidateSii(id) {
  const K = `valida-${id}`;
  showToast("Validando en SII…", "info", { key: K, persist: true });
  try {
    const res = await fetch(validarSiiUrl(id), {
      method: "POST",
      headers: { "X-CSRFToken": csrftoken, Accept: "application/json" },
      credentials: "include",
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data?.detail || `HTTP ${res.status}`);
    showToast(`TrackID: ${data?.result?.track_id || "—"}`, "success", {
      key: K,
      duration: 6000,
    });

    document.dispatchEvent(new Event("docs:reload"));

    const tid = data?.result?.track_id;
    if (tid) {
      // Polling breve para ver si cambia estado rápido
      for (let i = 0; i < 3; i++) {
        await new Promise((r) => setTimeout(r, 5000));
        await onRefreshSii(id, { silent: i < 2 });
      }
    }
  } catch (err) {
    showToast(`Error validando en SII: ${String(err)}`, "error", {
      key: K,
      duration: 7000,
    });
  }
}

async function onRefreshSii(id, { silent = false } = {}) {
  try {
    const dRes = await fetch(`${listUrl}${id}/`, {
      headers: { Accept: "application/json" },
      credentials: "include",
    });
    const d = await dRes.json().catch(() => null);
    if (!d?.sii_track_id) {
      if (!silent)
        showToast("Primero valida el documento para obtener Track ID.", "warning");
      return;
    }
  } catch (_) { }

  const K = `estado-${id}`;
  if (!silent)
    showToast("Consultando estado SII…", "info", { key: K, persist: true });
  try {
    const res = await fetch(estadoSiiUrl(id), {
      headers: { Accept: "application/json" },
      credentials: "include",
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data?.detail || `HTTP ${res.status}`);
    if (!silent)
      showToast(`Estado SII: ${data?.result?.estado || "—"}`, "success", {
        key: K,
        duration: 4000,
      });
    document.dispatchEvent(new Event("docs:reload"));
  } catch (err) {
    if (!silent)
      showToast(`Error consultando SII: ${String(err)}`, "error", {
        key: K,
        duration: 6000,
      });
  }
}

/* =======================
    Utilidades UI
   ======================= */

function escapeHtml(str) {
  if (str == null) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatValue(v, key = "") {
  if (v === null || v === undefined || v === "") {
    return `<span class="text-muted">—</span>`;
  }

  if (typeof v === "boolean") {
    return v
      ? `<span class="text-success">Sí</span>`
      : `<span class="text-danger">No</span>`;
  }

  if (typeof v === "number") {
    if (isMoneyKey(key)) {
      return fmtMoney(v); 
    }
    if (key === "folio") {
      return v.toString();
    }
    return fmtNumber(v); 
  }

  if (typeof v === "string") {
    // Detección simple de fecha ISO
    const dateMatch = v.match(/^(\d{4}-\d{2}-\d{2})T?([\d:.]+)?Z?$/);
    if (dateMatch) {
      const d = new Date(v);
      if (!isNaN(d.getTime())) {
        const hasTime = dateMatch[2] || v.includes("T");
        const options = { year: "numeric", month: "2-digit", day: "2-digit" };
        if (hasTime) {
          options.hour = "2-digit";
          options.minute = "2-digit";
        }
        const formatted = d.toLocaleString("es-CL", options);
        return `<span class="text-date">${formatted}</span>`;
      }
    }
    
    // Detectar JSON stringificado
    if (v.startsWith("{") && v.endsWith("}")) {
      try {
        const obj = JSON.parse(v);
        return `<pre class="json-display">${escapeHtml(JSON.stringify(obj, null, 2))}</pre>`;
      } catch (e) { }
    }

    return escapeHtml(v).replace(/\n/g, "<br>");
  }

  if (typeof v === "object") {
     try {
        return `<pre class="json-display">${escapeHtml(JSON.stringify(v, null, 2))}</pre>`;
      } catch { }
  }
  
  return escapeHtml(String(v));
}

function setPill(el, text, kind) {
  if (!el) return;
  if (!text) {
    el.hidden = true;
    return;
  }
  el.hidden = false;
  el.className = `pill ${kind || ""}`;
  el.textContent = text;
}