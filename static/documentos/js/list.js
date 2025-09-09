// static/panel/js/documentos/list.js
import { listUrl } from "./api.js";

const tbody = () => document.getElementById("documentsTableBody");

export function wireFilters(){
  document.getElementById("btnFilter")?.addEventListener("click", loadDocuments);

  // —— disparos robustos de carga inicial y retorno desde historial ——
  function bootLoad(){ try { loadDocuments(); } catch (_) {} }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bootLoad, { once: true });
  } else {
    bootLoad();
  }
  // bfcache (volver con atrás) + cuando la pestaña vuelve a estar visible
  window.addEventListener("pageshow", bootLoad);
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") bootLoad();
  });

  // también recarga cuando el módulo de subida termina
  document.addEventListener("docs:reload", loadDocuments);
}

export async function loadDocuments(){
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
  try{
    const res = await fetch(`${listUrl}?${params.toString()}`, { headers:{ Accept:"application/json" } });
    if (!res.ok) throw new Error("Respuesta inválida");
    const { results=[] } = await res.json();

    if (!results.length){ tbody().innerHTML=""; if (empty) empty.hidden=false; }
    else { if (empty) empty.hidden=true; renderRows(results); }

    const info = document.getElementById("result-info");
    if (info) info.textContent = results.length ? `${results.length} resultados` : "Sin resultados";
  }catch(e){
    tbody().innerHTML = `<tr><td colspan="7">Error al cargar documentos</td></tr>`;
    if (empty) empty.hidden = true;
  }
}

function renderRows(rows){
  const fmtCLP = v => v==null ? "—" : new Intl.NumberFormat("es-CL",{style:"currency",currency:"CLP",maximumFractionDigits:0}).format(v);
  tbody().innerHTML = rows.map(r=>`
    <tr id="doc-row-${r.id}" data-doc-id="${r.id}" data-estado="${r.estado}">
      <td class="col-fecha">${r.fecha || "—"}</td>
      <td class="col-tipo">${r.tipo || "—"}</td>
      <td class="col-folio">${r.folio || "—"}</td>
      <td class="col-rut">${r.rut_emisor || "—"}</td>
      <td class="col-razon">${r.razon_social || "—"}</td>
      <td class="col-total num">${fmtCLP(r.total)}</td>
      <td class="col-estado"><span class="badge ${
        r.estado==="procesado"||r.estado==="validado"?"badge-success":
        (r.estado==="cola"||r.estado==="pendiente"||r.estado==="procesando")?"badge-warning":"badge-error"
      }">${r.estado || "—"}</span></td>
      <td class="col-sii">${r.validado_sii ? (r.sii_estado || "OK") : "—"}</td>
      <td class="actions">
        ${r.archivo?`<a class="act" href="${r.archivo}" target="_blank" rel="noopener" style="color: black;"><i class="fa-solid fa-eye fa-xl"></i></a>`:""}
        <a class="act" href="#" style="color: black;"><i class="fa-solid fa-download fa-xl"></i></a>
      </td>
    </tr>`).join("");

  // notificar a progreso.js que hay nueva renderización
  document.dispatchEvent(new Event("docs:rendered"));
}