// static/panel/js/documentos/list.js
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

export function wireFilters() {
  document.getElementById("btnFilter")?.addEventListener("click", loadDocuments);

  // carga inicial + retorno de historial
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

  // click en filas y en acciones
  document
    .getElementById("documentsTable")
    ?.addEventListener("click", async (e) => {
      const act = e.target?.closest?.(".act");
      if (act) {
        e.preventDefault();
        e.stopPropagation();
        const id =
          act.dataset.id || act.closest("tr")?.getAttribute("data-doc-id");
        if (!id) return;
        if (act.classList.contains("act-validate")) return onValidateSii(id);
        if (act.classList.contains("act-refresh")) return onRefreshSii(id);
        if (act.classList.contains("act-open")) return; // enlaces normales
        return;
      }
      const tr = e.target.closest("tr[data-doc-id]");
      if (tr) {
        const id = tr.getAttribute("data-doc-id");
        openDetailModal(id);
      }
    });

  // auto-refresh suave: si hay filas “validando…”, actualizar cada 10s
  setInterval(() => {
    const anyProcessing = !!document.querySelector(
      "#documentsTable .badge--info"
    );
    if (anyProcessing) document.dispatchEvent(new Event("docs:reload"));
  }, 10000);
}

export async function loadDocuments() {
  // filtros
  const dateFrom = document.getElementById("filterDateFrom")?.value || "";
  const dateTo = document.getElementById("filterDateTo")?.value || "";
  const docType = document.getElementById("filterType")?.value || "";
  const docStatus = document.getElementById("filterStatus")?.value || "";

  const params = new URLSearchParams();
  if (dateFrom) params.set("dateFrom", dateFrom);
  if (dateTo) params.set("dateTo", dateTo);
  if (docType) params.set("docType", docType);
  if (docStatus) params.set("docStatus", docStatus);

  // --- 1. OBTENER REFERENCIAS ---
  const tb = tbody();
  const empty = document.getElementById("tbl-empty");
  const skeleton = document.getElementById("tbl-skeleton");

  // --- 2. ESTADO DE CARGA ---
  // Ocultar "vacío", mostrar "skeleton" y limpiar la tabla de datos viejos.
  if (tb) tb.innerHTML = "";
  
  // [MEJORA] Forzar ocultado del estado vacío
  if (empty) {
      empty.hidden = true;
      empty.style.display = 'none'; 
  }
  
  if (skeleton) skeleton.hidden = false;

  try {
    const res = await fetch(`${listUrl}?${params.toString()}`, {
      headers: { Accept: "application/json" },
      credentials: "include",
    });

    // --- 3. CARGA FINALIZADA ---
    // Ocultar "skeleton" SIEMPRE, ya sea éxito o error.
    if (skeleton) skeleton.hidden = true;

    if (!res.ok) {
      throw new Error(`Respuesta inválida (${res.status})`);
    }

    const { results = [] } = await res.json();

    // refrescar cache
    docCache.clear();
    results.forEach((r) => {
      if (r?.id != null) docCache.set(String(r.id), r);
    });

    // --- 4. MOSTRAR RESULTADOS O ESTADO VACÍO ---
    if (!results.length) {
      // No hay resultados: Ocultar tabla, mostrar "vacío"
      if (tb) tb.innerHTML = "";
      // [MEJORA] Mostrar estado vacío y limpiar estilo inline
      if (empty) {
          empty.hidden = false;
          empty.style.display = ''; 
      }
    } else {
      // Hay resultados: Ocultar "vacío", renderizar filas en la tabla
      // [MEJORA] Asegurar que vacío esté oculto
      if (empty) {
          empty.hidden = true;
          empty.style.display = 'none'; 
      }
      renderRows(results);
    }

    // Actualizar contador
    const info = document.getElementById("result-info");
    if (info)
      info.textContent = results.length
        ? `${results.length} resultados`
        : "Sin resultados";

  } catch (e) {
    // --- 5. MANEJO DE ERROR ---
    console.error("Error al cargar documentos:", e);
    if (skeleton) skeleton.hidden = true; // Ocultar skeleton
    
    // [MEJORA] Asegurar que vacío esté oculto si mostramos error en tabla
    if (empty) {
        empty.hidden = true;
        empty.style.display = 'none';
    }
    
    // Mostrar un error dentro del cuerpo de la tabla
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
// LÓGICA DEL MODAL
// =================================================================

// --- 1. Definición de Etiquetas y Formato ---

// Formateador de moneda
const fmtMoney = (n) =>
  n == null
    ? "—"
    : new Intl.NumberFormat("es-CL", {
        style: "currency",
        currency: "CLP",
        maximumFractionDigits: 0,
      }).format(n);

// Formateador de número simple
const fmtNumber = (n) =>
  n == null ? "—" : new Intl.NumberFormat("es-CL").format(n);

// Mapa de etiquetas para traducir claves de la API
const LABELS = {
  // Clave de API : [Etiqueta legible, Grupo]
  tipo_documento: ["Tipo de Documento", "principal"],
  folio: ["Folio", "principal"],
  rut_proveedor: ["RUT Proveedor", "principal"],
  nombre_proveedor: ["Razón Social", "principal"],
  rut_emisor: ["RUT Proveedor", "principal"], // Alias
  razon_social: ["Razón Social", "principal"], // Alias

  fecha_emision: ["Fecha Emisión", "fechas"],
  fecha_vencimiento: ["Fecha Vencimiento", "fechas"],
  fecha_recepcion: ["Fecha Recepción", "fechas"],
  fecha: ["Fecha Emisión", "fechas"], // Alias
  created_at: ["Fecha Creación", "fechas"],

  monto_neto: ["Neto", "montos"],
  neto: ["Neto", "montos"], // Alias
  monto_exento: ["Exento", "montos"],
  exento: ["Exento", "montos"], // Alias
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

// Función para saber si una clave es de dinero
function isMoneyKey(key) {
  return ["monto_neto", "neto", "monto_exento", "exento", "iva", "total"].includes(key);
}

// --- 2. Lógica para construir y mostrar el modal ---

function openDetailModal(docId) {
  const doc = docCache.get(String(docId));
  if (!doc) {
    console.error("No se encontró el documento en caché:", docId);
    return;
  }

  // Limpiar contenido anterior y mostrar esqueleto
  $content().innerHTML = `
    <div class="kv-skel">
      <div class="skeleton"></div><div class="skeleton"></div>
      <div class="skeleton"></div><div class="skeleton"></div>
      <div class="skeleton"></div><div class="skeleton"></div>
    </div>`;

  // Construir y mostrar el contenido real
  paintDetail(doc, false); // false = no es solo un refresco

  // Abrir modal
  $overlay().style.display = "flex";
  $overlay().setAttribute("aria-hidden", "false");

  // Buscar detalles completos en segundo plano
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
  // Si ya tenemos el 'nombre_archivo', asumimos que es el detalle completo
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
  } catch (_) {
    /* silencioso */
  }
}

/**
 * Pinta el contenido del modal.
 * Si isRefresh=true, solo actualiza el contenido.
 * Si isRefresh=false, actualiza todo (contenido, botones, pills).
 */
function paintDetail(doc, isRefresh = false) {
  
  // 1. Construir y mostrar el contenido principal
  const modalHtml = buildModalContent(doc);
  $content().innerHTML = modalHtml;

  // Si es la carga inicial (no un refresco), también configurar botones y pills
  if (isRefresh) return;

  // 2. Pills estado y SII
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

  // 3. Acciones (Botones Ver/Descargar)
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

/**
 * Construye el HTML del modal basado en los datos
 * y el mapa de etiquetas (LABELS).
 */
function buildModalContent(data) {
  const groups = {
    principal: [],
    fechas: [],
    montos: [],
    detalle: [],
    meta: [],
    otros: [], // Para cualquier clave no definida en LABELS
  };

  // Claves conocidas que no queremos en "Otros Datos" (ya se muestran en pills/botones)
  const knownKeys = new Set([
      'estado', 'sii_estado', 'sii_track_id', 'validado_sii', 'archivo',
  ]);

  // 1. Clasificar todos los datos en grupos
  for (const [key, value] of Object.entries(data)) {
    if (value === null || value === "" || knownKeys.has(key)) continue; // Omitir nulos, vacíos o conocidos

    const [label, group] = LABELS[key] || [key, 'otros'];

    // Si el grupo es 'otros', formateamos la clave (ej: "mi_clave_rara" -> "Mi Clave Rara")
    const finalLabel =
      group === "otros"
        ? key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())
        : label;

    groups[group].push({
      key: finalLabel,
      value: formatValue(value, key), // Pasamos la clave original para formateo
    });
  }

  // 2. Construir el HTML
  let html = "";

  // Añadimos el título principal (que antes estaba en el header)
  // Usamos el ID "docDetailTitle" para accesibilidad (aria-labelledby)
  const tipoDoc = data.tipo_documento || data.tipo || "Documento";
  const folio = data.folio || data.id;
  html += `<h3 id="docDetailTitle" class="detail-section-title">${tipoDoc} #${folio}</h3>`;

  // Añadir secciones que tengan contenido
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
    
    // Evitar duplicados (ej: si 'rut_proveedor' y 'rut_emisor' están, solo mostrar uno)
    const uniqueItems = Array.from(new Map(items.map(item => [item.key, item])).values());
    
    if (uniqueItems.length > 0) {
      // No añadir el título de "Información Principal" si ya pusimos el título del documento
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
    Acciones SII (fetch)
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

    // recarga lista para reflejar sii_estado/sii_track_id
    document.dispatchEvent(new Event("docs:reload"));

    // auto seguimiento (solo si hay track)
    const tid = data?.result?.track_id;
    if (tid) {
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
  // protección: evitar 400 si no hay track
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
  } catch (_) {
    /* ignore */
  }

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

/**
 * Formatea un valor para mostrar en el modal.
 * AHORA ACEPTA LA CLAVE (key) para un formato inteligente.
 */
function formatValue(v, key = "") {
  if (v === null || v === undefined || v === "") {
    return `<span class="text-muted">—</span>`;
  }

  // 1. Booleanos
  if (typeof v === "boolean") {
    return v
      ? `<span class="text-success">Sí</span>`
      : `<span class="text-danger">No</span>`;
  }

  // 2. Números (¡AHORA DISTINGUE MONEDA!)
  if (typeof v === "number") {
    if (isMoneyKey(key)) {
      return fmtMoney(v); // <--- ¡Formato de Peso Chileno!
    }
    // No formatear el folio como número con separador de miles
    if (key === "folio") {
      return v.toString();
    }
    return fmtNumber(v); // <--- Formato de número estándar
  }

  // 3. Manejo de cadenas (detección de fechas)
  if (typeof v === "string") {
    // Intenta detectar un formato de fecha ISO
    const dateMatch = v.match(/^(\d{4}-\d{2}-\d{2})T?([\d:.]+)?Z?$/);
    if (dateMatch) {
      const d = new Date(v);
      if (!isNaN(d.getTime())) {
        const hasTime = dateMatch[2] || v.includes("T");
        // Usamos 'es-CL' para el formato de fecha
        const options = { year: "numeric", month: "2-digit", day: "2-digit" };
        if (hasTime) {
          options.hour = "2-digit";
          options.minute = "2-digit";
        }

        const formatted = d.toLocaleString("es-CL", options);
        return `<span class="text-date">${formatted}</span>`;
      }
    }
    
    // Si es un objeto JSON en string
    if (v.startsWith("{") && v.endsWith("}")) {
      try {
        const obj = JSON.parse(v);
        return `<pre class="json-display">${escapeHtml(JSON.stringify(obj, null, 2))}</pre>`;
      } catch (e) { /* no es json, sigue */ }
    }

    // Cadena normal: escapar HTML
    return escapeHtml(v).replace(/\n/g, "<br>");
  }

  // Fallback para otros tipos (ej: arrays u objetos)
  if (typeof v === "object") {
     try {
        return `<pre class="json-display">${escapeHtml(JSON.stringify(v, null, 2))}</pre>`;
      } catch { /* sigue */ }
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