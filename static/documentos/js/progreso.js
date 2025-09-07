(function () {
  const POLL_MS = 5000;
  let polling = false; // evita loops duplicados

  function getPendingIds() {
    const rows = document.querySelectorAll(
      'tr[data-estado="pendiente"], tr[data-estado="procesando"]'
    );
    const ids = [];
    rows.forEach((r) => {
      const id = r.getAttribute("data-doc-id");
      if (id) ids.push(id);
    });
    return ids;
  }

  function formatMoney(n) {
    if (n === null || n === undefined) return "—";
    try {
      return new Intl.NumberFormat("es-CL", {
        style: "currency",
        currency: "CLP",
        maximumFractionDigits: 0,
      }).format(n);
    } catch {
      return "$" + n;
    }
  }

  function updateRow(doc) {
    const row = document.getElementById(`doc-row-${doc.id}`);
    if (!row) return;

    // Actualiza columnas si vinieron datos nuevos
    if (doc.fecha_emision)
      row.querySelector(".col-fecha").textContent = doc.fecha_emision;
    if (doc.tipo_documento)
      row.querySelector(".col-tipo").textContent =
        doc.tipo_documento || "desconocido";
    if (doc.folio)
      row.querySelector(".col-folio").textContent = doc.folio || "—";
    if (doc.rut_proveedor)
      row.querySelector(".col-rut").textContent = doc.rut_proveedor || "—";
    if (doc.total !== undefined)
      row.querySelector(".col-total").textContent = formatMoney(doc.total);

    // Estado/badge
    const badge = row.querySelector(".col-estado .badge");
    if (badge) {
      badge.textContent = doc.estado;
      badge.className = `badge badge-${doc.estado}`;
    }
    row.setAttribute("data-estado", doc.estado);
  }

  async function pollBatch(ids) {
    if (!ids.length) return { ok: true, documentos: [] };
    const url = `/documentos/progreso_batch/?ids=${ids.join(",")}`;
    const r = await fetch(url, { credentials: "same-origin" });
    return r.json();
  }

  async function tick() {
    const ids = getPendingIds();
    if (!ids.length) { polling = false; return; } // nada pendiente, detener

    try {
      const data = await pollBatch(ids);
      if (data.ok) {
        data.documentos.forEach(updateRow);
      }
    } catch (e) {
      console.warn("Polling error:", e);
    } finally {
      // Reprograma solo si aún hay pendientes
      if (getPendingIds().length) {
        setTimeout(tick, POLL_MS);
      } else {
        polling = false;
      }
    }
  }

  // Arranca al cargar si hay pendientes
  document.addEventListener("DOMContentLoaded", () => {
    if (getPendingIds().length && !polling) { polling = true; setTimeout(tick, POLL_MS); }
  });

  // Arranca tras cada re-render de la tabla (lo dispara list.js)
  document.addEventListener("docs:rendered", () => {
    if (getPendingIds().length && !polling) { polling = true; setTimeout(tick, POLL_MS); }
  });
})();
