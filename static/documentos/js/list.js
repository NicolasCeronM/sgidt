// static/panel/js/documentos/list.js
import { listUrl } from "./api.js";

const tbody = () => document.getElementById("documentsTableBody");

// cache simple por id para reutilizar los datos ya listados
const docCache = new Map();

// refs del modal
const $overlay  = () => document.getElementById("docDetailOverlay");
const $title    = () => document.getElementById("docDetailTitle");
const $content  = () => document.getElementById("docDetailContent");
const $closeBtn = () => document.getElementById("docDetailClose");
const $viewBtn  = () => document.getElementById("docViewBtn");
const $dlBtn    = () => document.getElementById("docDownloadBtn");
const $pillE    = () => document.getElementById("docEstadoPill");
const $pillSII  = () => document.getElementById("docSiiPill");

export function wireFilters() {
  document.getElementById("btnFilter")?.addEventListener("click", loadDocuments);

  // carga inicial + retorno de historial
  function bootLoad(){ try { loadDocuments(); } catch(_){} }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", bootLoad, { once:true });
  else bootLoad();
  window.addEventListener("pageshow", bootLoad);
  document.addEventListener("visibilitychange", () => { if (document.visibilityState === "visible") bootLoad(); });
  document.addEventListener("docs:reload", loadDocuments);

  // click en filas y en acciones
  document.getElementById("documentsTable")?.addEventListener("click", (e) => {
    const a = e.target.closest("a.act");
    if (a) { e.stopPropagation(); return; } // las acciones de la tabla no abren el modal
    const tr = e.target.closest("tr[data-doc-id]");
    if (tr) {
      const id = tr.getAttribute("data-doc-id");
      openDetailModal(id);
    }
  });

  // cerrar modal
  $closeBtn()?.addEventListener("click", closeModal);
  $overlay()?.addEventListener("click", (e) => {
    if (e.target === $overlay()) closeModal();
  });
  document.addEventListener("keydown", (e) => {
    if ($overlay()?.getAttribute("aria-hidden")==="false" && e.key === "Escape") closeModal();
  });
}

export async function loadDocuments() {
  const dateFrom = document.getElementById("dateFrom")?.value;
  const dateTo   = document.getElementById("dateTo")?.value;
  const docType  = document.getElementById("docType")?.value;
  const docStatus= document.getElementById("docStatus")?.value;

  const params = new URLSearchParams();
  if (dateFrom) params.set("dateFrom", dateFrom);
  if (dateTo)   params.set("dateTo", dateTo);
  if (docType)  params.set("docType", docType);
  if (docStatus)params.set("docStatus", docStatus);

  const empty = document.getElementById("tbl-empty");
  try {
    const res = await fetch(`${listUrl}?${params.toString()}`, { headers: { Accept: "application/json" }});
    if (!res.ok) throw new Error("Respuesta inválida");
    const { results = [] } = await res.json();

    // refrescar cache
    docCache.clear();
    results.forEach(r => { if (r?.id != null) docCache.set(String(r.id), r); });

    if (!results.length) {
      tbody().innerHTML = "";
      if (empty) empty.hidden = false;
    } else {
      if (empty) empty.hidden = true;
      renderRows(results);
    }

    const info = document.getElementById("result-info");
    if (info) info.textContent = results.length ? `${results.length} resultados` : "Sin resultados";
  } catch (e) {
    tbody().innerHTML = `<tr><td colspan="9">Error al cargar documentos</td></tr>`;
    if (empty) empty.hidden = true;
  }
}

function renderRows(rows) {
  const fmtCLP = (v) =>
    v == null
      ? "—"
      : new Intl.NumberFormat("es-CL", {
          style: "currency",
          currency: "CLP",
          maximumFractionDigits: 0,
        }).format(v);

  tbody().innerHTML = rows.map((r) => `
    <tr id="doc-row-${r.id}" data-doc-id="${r.id}" data-estado="${r.estado}">
      <td class="col-fecha">${r.fecha || r.fecha_emision || "—"}</td>
      <td class="col-tipo">${r.tipo || r.tipo_documento || "—"}</td>
      <td class="col-folio">${r.folio || "—"}</td>
      <td class="col-rut">${r.rut_emisor || r.rut_proveedor || "—"}</td>
      <td class="col-razon">${r.razon_social || r.razon_social_proveedor || "—"}</td>
      <td class="col-total num">${fmtCLP(r.total)}</td>
      <td class="col-estado">
        <span class="badge ${
          r.estado === "procesado" || r.estado === "validado"
            ? "badge-success"
            : ["cola","pendiente","procesando"].includes(r.estado)
            ? "badge-warning"
            : "badge-error"
        }">${r.estado || "—"}</span>
      </td>
      <td class="col-sii">${r.validado_sii ? (r.sii_estado || "OK") : "—"}</td>
      <td class="actions">
        ${ r.archivo ? `<a class="act" href="${r.archivo}" target="_blank" rel="noopener" style="color:black;"><i class="fa-solid fa-eye fa-xl"></i></a>` : "" }
        ${ r.archivo ? `<a class="act" href="${r.archivo}" download style="color:black;"><i class="fa-solid fa-download fa-xl"></i></a>` : "" }
      </td>
    </tr>
  `).join("");

  // notificar a progreso.js que hay nueva renderización
  document.dispatchEvent(new Event("docs:rendered"));
}

/* ==========================
   MODAL: abrir, pintar y fetch
   ========================== */
function openModal() {
  const ov = $overlay(); if (!ov) return;
  ov.setAttribute("aria-hidden", "false");
  // focus accesible
  setTimeout(() => ov.querySelector(".modal")?.focus(), 10);
}
function closeModal() {
  $overlay()?.setAttribute("aria-hidden", "true");
}

function setPill(el, text, kind){ if(!el) return; el.textContent = text; el.className = `pill ${kind}`; el.hidden = !text; }

function kvGridFromObject(obj){
  const entries = Object.entries(obj ?? {});
  if(!entries.length) return `<p>No hay datos.</p>`;
  return `
    <div class="kv-grid">
      ${entries.map(([k,v]) => `
        <div class="k">${escapeHtml(k)}</div>
        <div class="v">${formatValue(v)}</div>
      `).join("")}
    </div>
  `;
}

function formatValue(v){
  if (v == null) return "—";
  if (typeof v === "object") {
    try { return `<pre style="white-space:pre-wrap;margin:.25rem 0 .5rem 0">${escapeHtml(JSON.stringify(v, null, 2))}</pre>`; }
    catch { return String(v); }
  }
  if (typeof v === "number") {
    // heurística: si parece CLP (>= 1000) muestra con formato local
    if (Math.abs(v) >= 1000) {
      return new Intl.NumberFormat("es-CL", { style: "currency", currency: "CLP", maximumFractionDigits: 0 }).format(v);
    }
  }
  return escapeHtml(String(v));
}

function escapeHtml(s){ return s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }

async function openDetailModal(id){
  // 1) mostrar modal con esqueleto
  $title().textContent = "Detalle del documento";
  $content().innerHTML = `
    <div class="kv-skel">
      <div class="skeleton"></div><div class="skeleton"></div>
      <div class="skeleton"></div><div class="skeleton"></div>
      <div class="skeleton"></div><div class="skeleton"></div>
      <div class="skeleton"></div><div class="skeleton"></div>
    </div>`;
  setPill($pillE(), "", ""); setPill($pillSII(), "", "");
  $viewBtn().hidden = true; $dlBtn().hidden = true;
  openModal();

  // 2) pintar rápido con lo que tenemos en cache
  const cached = docCache.get(String(id));
  if (cached) {
    paintDetail(cached);
  }

  // 3) intentar ampliar con detalle desde API (si existe retrieve)
  try{
    const res = await fetch(`${listUrl}${id}/`, { headers: { Accept: "application/json" }});
    if (res.ok){
      const full = await res.json();
      // merge superficial
      const merged = { ...(cached||{}), ...(full||{}) };
      docCache.set(String(id), merged);
      paintDetail(merged);
    }
  }catch(_){ /* silencioso */ }
}

function paintDetail(doc){
  // título
  const folio = doc.folio ? ` #${doc.folio}` : "";
  const tipo  = doc.tipo_documento || doc.tipo || "Documento";
  const fecha = doc.fecha_emision || doc.fecha || "";
  $title().textContent = `${tipo}${folio}${fecha ? " · " + fecha : ""}`;

  // pills estado y SII
  if (doc.estado){
    const kind = (doc.estado==="procesado"||doc.estado==="validado") ? "ok"
               : (["cola","pendiente","procesando"].includes(doc.estado)) ? "warn" : "err";
    setPill($pillE(), `Estado: ${doc.estado}`, kind);
  } else setPill($pillE(), "", "");

  if ("validado_sii" in doc){
    const k = doc.validado_sii ? "ok" : "warn";
    const t = doc.validado_sii ? (doc.sii_estado || "SII OK") : "No validado SII";
    setPill($pillSII(), t, k);
  } else setPill($pillSII(), "", "");

  // acciones
  if (doc.archivo){
    $viewBtn().href = doc.archivo; $viewBtn().hidden = false;
    $dlBtn().href   = doc.archivo; $dlBtn().hidden   = false;
  } else { $viewBtn().hidden = true; $dlBtn().hidden = true; }

  // contenido dinámico con todos los campos
  $content().innerHTML = kvGridFromObject(doc);
}
