(function () {
  const POLL_MS = 5000;
  let polling = false;

  const batchUrl = (ids) => `/api/documentos/progreso_batch/?ids=${ids.join(",")}`;

  function getPendingIds() {
    return Array.from(document.querySelectorAll('tr[data-estado="pendiente"], tr[data-estado="procesando"]'))
      .map(r => r.getAttribute("data-doc-id"))
      .filter(Boolean);
  }

  const fmtMoney = (n) => n==null ? "—" : new Intl.NumberFormat("es-CL",{style:"currency",currency:"CLP",maximumFractionDigits:0}).format(n);

  function applyBadgeClass(el, estado) {
    let cls = "badge-error";
    if (estado === "procesado" || estado === "validado") cls = "badge-success";
    else if (["cola","pendiente","procesando"].includes(estado)) cls = "badge-warning";
    el.className = `badge ${cls}`;
  }

  function setText(sel, row, val) {
    const el = row.querySelector(sel);
    if (el) el.textContent = (val ?? val === 0) ? val : "—";
  }

  function updateRow(doc) {
    const row = document.getElementById(`doc-row-${doc.id}`);
    if (!row) return;

    setText(".col-fecha",  row, doc.fecha_emision || "—");
    setText(".col-tipo",   row, doc.tipo_documento || "desconocido");
    setText(".col-folio",  row, doc.folio || "—");
    setText(".col-rut",    row, doc.rut_proveedor || "—");

    if ("razon_social_proveedor" in doc) setText(".col-razon", row, doc.razon_social_proveedor || "—");
    if ("monto_neto"      in doc) setText(".col-neto",   row, fmtMoney(doc.monto_neto));
    if ("monto_exento"    in doc) setText(".col-exento", row, fmtMoney(doc.monto_exento));
    if ("iva"             in doc) setText(".col-iva",    row, fmtMoney(doc.iva));
    if ("total"           in doc) setText(".col-total",  row, fmtMoney(doc.total));

    // Estado
    const badge = row.querySelector(".col-estado .badge");
    if (badge && doc.estado) { badge.textContent = doc.estado; applyBadgeClass(badge, doc.estado); }
    if (doc.estado) row.setAttribute("data-estado", doc.estado);

    // Validación SII (si viene)
    if ("validado_sii" in doc || "sii_estado" in doc) {
      setText(".col-sii", row, doc.validado_sii ? (doc.sii_estado || "OK") : "—");
    }
  }

  async function pollBatch(ids) {
    if (!ids.length) return { ok: true, documentos: [] };
    const r = await fetch(batchUrl(ids), { credentials: "same-origin" });
    return r.json();
  }

  async function tick() {
    const ids = getPendingIds();
    if (!ids.length) { polling = false; return; }

    try {
      const data = await pollBatch(ids);
      if (data.ok) data.documentos.forEach(updateRow);
    } finally {
      if (getPendingIds().length) setTimeout(tick, POLL_MS);
      else polling = false;
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    if (getPendingIds().length && !polling) { polling = true; setTimeout(tick, POLL_MS); }
  });
  document.addEventListener("docs:rendered", () => {
    if (getPendingIds().length && !polling) { polling = true; setTimeout(tick, POLL_MS); }
  });
})();
