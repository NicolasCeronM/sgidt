// static/panel/js/documentos/list.js
import { listUrl, csrftoken } from "./api.js";
import { showToast } from "./ui.js";

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

// builders para acciones SII
const validarSiiUrl = (id) => `/api/v1/documentos/${id}/validar-sii/`;
const estadoSiiUrl  = (id) => `/api/v1/documentos/${id}/estado-sii/`;

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
  document.getElementById("documentsTable")?.addEventListener("click", async (e) => {
    const act = e.target?.closest?.(".act");
    if (act) {
      e.preventDefault(); e.stopPropagation();
      const id = act.dataset.id || act.closest("tr")?.getAttribute("data-doc-id");
      if (!id) return;
      if (act.classList.contains("act-validate"))      return onValidateSii(id);
      if (act.classList.contains("act-refresh"))       return onRefreshSii(id);
      if (act.classList.contains("act-open"))          return; // enlaces normales
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
    const anyProcessing = !!document.querySelector("#documentsTable .badge--info");
    if (anyProcessing) document.dispatchEvent(new Event("docs:reload"));
  }, 10000);
}

export async function loadDocuments(){
  // filtros
  const dateFrom  = document.getElementById("filterDateFrom")?.value || "";
  const dateTo    = document.getElementById("filterDateTo")?.value   || "";
  const docType   = document.getElementById("filterType")?.value     || "";
  const docStatus = document.getElementById("filterStatus")?.value   || "";

  const params = new URLSearchParams();
  if (dateFrom) params.set("dateFrom", dateFrom);
  if (dateTo)   params.set("dateTo", dateTo);
  if (docType)  params.set("docType", docType);
  if (docStatus)params.set("docStatus", docStatus);

  const empty = document.getElementById("tbl-empty");
  try {
    const res = await fetch(`${listUrl}?${params.toString()}`, { headers: { Accept: "application/json" }, credentials: "include" });
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

function renderSiiBadge(r){
  const est = (r.sii_estado || "").toUpperCase();
  if (!est) return "—";
  if (est === "EN_PROCESO" || est === "RECIBIDO") {
    return `<span class="badge badge--info">
      <i class="fa-solid fa-circle-notch fa-spin" style="margin-right:6px"></i>
      validando…
    </span>`;
  }
  if (est === "ACEPTADO")  return `<span class="badge badge--success">aceptado</span>`;
  if (est === "RECHAZADO") return `<span class="badge badge--danger">rechazado</span>`;
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
      <td>${fmtCLP(r.total)}</td>
      <td>
        ${r.estado ? `<span class="badge ${r.estado==="procesado"||r.estado==="validado" ? "badge--success" :
                                     (["cola","pendiente","procesando"].includes(r.estado) ? "badge--info" : "badge--danger")}">${escapeHtml(r.estado)}</span>` : "—"}
      </td>
      <td>${renderSiiBadge(r)}</td>
      <td class="actions">
        ${ r.archivo ? `<a class="act act-open" href="${r.archivo}" target="_blank" rel="noopener" title="Ver"><i class="fa-solid fa-eye fa-xl"></i></a>` : "" }
        ${ r.archivo ? `<a class="act act-open" href="${r.archivo}" download title="Descargar"><i class="fa-solid fa-download fa-xl"></i></a>` : "" }

        <!-- Validar SII: siempre disponible para reintento -->
        <a class="act act-validate" href="#" data-id="${r.id}" title="Validar en SII" aria-label="Validar en SII">
          <i class="fa-solid fa-shield-check fa-xl"></i>
        </a>

        <!-- Actualizar estado SII: solo si hay TrackID -->
        ${ r.sii_track_id ? `
          <a class="act act-refresh" href="#" data-id="${r.id}" title="Actualizar estado SII" aria-label="Actualizar estado SII">
            <i class="fa-solid fa-rotate fa-xl"></i>
          </a>` : `
          <span class="act disabled" title="Valida primero para obtener Track ID" aria-label="Sin Track ID">
            <i class="fa-solid fa-rotate fa-xl" style="opacity:.35;pointer-events:none"></i>
          </span>`
        }
      </td>
    </tr>
  `).join("");

  tbody().innerHTML = html;
}

function openDetailModal(id){
  const d = docCache.get(String(id));
  if(!d) return;
  $overlay().style.display = "flex";
  paintDetail(d);
  fetchDetailIfNeeded(id);
}
function closeDetailModal(){ $overlay().style.display = "none"; }
$closeBtn()?.addEventListener("click", closeDetailModal);
$overlay()?.addEventListener("click", (e) => { if (e.target === $overlay()) closeDetailModal(); });

async function fetchDetailIfNeeded(id){
  const cached = docCache.get(String(id));
  try{
    const res = await fetch(`${listUrl}${id}/`, { headers:{ Accept:"application/json" }, credentials:"include" });
    if (res.ok){
      const full = await res.json();
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

  if ("validado_sii" in doc || "sii_estado" in doc){
    const est = (doc.sii_estado || "").toUpperCase();
    if (est === "ACEPTADO") setPill($pillSII(), "SII: aceptado", "ok");
    else if (est === "RECHAZADO") setPill($pillSII(), "SII: rechazado", "err");
    else if (est === "EN_PROCESO" || est === "RECIBIDO") setPill($pillSII(), "SII: validando…", "warn");
    else setPill($pillSII(), doc.validado_sii ? (doc.sii_estado || "SII OK") : "No validado SII", doc.validado_sii ? "ok" : "warn");
  } else setPill($pillSII(), "", "");

  // acciones
  if (doc.archivo){
    $viewBtn().href = doc.archivo; $viewBtn().hidden = false;
    $dlBtn().href   = doc.archivo; $dlBtn().hidden   = false;
  } else { $viewBtn().hidden = true; $dlBtn().hidden = true; }

  // contenido dinámico con todos los campos
  $content().innerHTML = kvGridFromObject(doc);
}

/* =======================
   Acciones SII (fetch)
   ======================= */
async function onValidateSii(id){
  const K = `valida-${id}`;
  showToast("Validando en SII…", "info", { key: K, persist: true });
  try{
    const res = await fetch(validarSiiUrl(id), {
      method: "POST",
      headers: { "X-CSRFToken": csrftoken, Accept: "application/json" },
      credentials: "include",
    });
    const data = await res.json().catch(()=>({}));
    if (!res.ok) throw new Error(data?.detail || `HTTP ${res.status}`);
    showToast(`TrackID: ${data?.result?.track_id || "—"}`, "success", { key: K, duration: 6000 });

    // recarga lista para reflejar sii_estado/sii_track_id
    document.dispatchEvent(new Event("docs:reload"));

    // auto seguimiento (solo si hay track)
    const tid = data?.result?.track_id;
    if (tid){
      for (let i=0; i<3; i++){
        await new Promise(r=>setTimeout(r, 5000));
        await onRefreshSii(id, { silent: i<2 });
      }
    }
  }catch(err){
    showToast(`Error validando en SII: ${String(err)}`, "error", { key: K, duration: 7000 });
  }
}

async function onRefreshSii(id, { silent=false } = {}){
  // protección: evitar 400 si no hay track
  try{
    const dRes = await fetch(`${listUrl}${id}/`, { headers:{Accept:"application/json"}, credentials:"include" });
    const d = await dRes.json().catch(()=>null);
    if (!d?.sii_track_id){
      if (!silent) showToast("Primero valida el documento para obtener Track ID.", "warning");
      return;
    }
  }catch(_){ /* ignore */ }

  const K = `estado-${id}`;
  if (!silent) showToast("Consultando estado SII…", "info", { key: K, persist: true });
  try{
    const res = await fetch(estadoSiiUrl(id), { headers: { Accept:"application/json" }, credentials:"include" });
    const data = await res.json().catch(()=>({}));
    if (!res.ok) throw new Error(data?.detail || `HTTP ${res.status}`);
    if (!silent) showToast(`Estado SII: ${data?.result?.estado || "—"}`, "success", { key: K, duration: 4000 });
    document.dispatchEvent(new Event("docs:reload"));
  }catch(err){
    if (!silent) showToast(`Error consultando SII: ${String(err)}`, "error", { key: K, duration: 6000 });
  }
}

/* =======================
   Utilidades UI
   ======================= */
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
    if (Math.abs(v) >= 1000) {
      return new Intl.NumberFormat("es-CL", { style: "currency", currency: "CLP", maximumFractionDigits: 0 }).format(v);
    }
  }
  return escapeHtml(String(v));
}

function setPill(el, text, kind){
  if(!el) return;
  if(!text){ el.hidden=true; return; }
  el.hidden=false;
  el.className = `pill ${kind||""}`;
  el.textContent = text;
}

function escapeHtml(s){
  return String(s).replace(/[&<>"'`=\/]/g, (c) => ({
    "&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;","/":"&#x2F;","`":"&#x60;","=":"&#x3D;"
  })[c]);
}
