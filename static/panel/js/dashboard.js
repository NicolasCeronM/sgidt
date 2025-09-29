// static/panel/js/dashboard.js

(function () {
  const fmtCL = new Intl.NumberFormat("es-CL");

  const elTitle = document.getElementById("db-title");
  const elDocs = document.querySelector('[data-kpi="docs_mes"]');
  const elIva  = document.querySelector('[data-kpi="iva_mes"]');
  const elGasto= document.querySelector('[data-kpi="gasto_mes"]');

  const elSkeleton = document.querySelector(".list-compact.skeleton");
  const elTimeline = document.querySelector(".list-compact.timeline");
  const cardsGrid  = document.querySelector(".cards-grid");

  function animateNumber(el, target, { prefix = "" } = {}) {
    const duration = 900;
    const start = performance.now();

    function tick(now) {
      const p = Math.min((now - start) / duration, 1);
      const val = Math.round(target * (0.2 + 0.8 * p));
      el.textContent = prefix + fmtCL.format(val);
      if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }

  async function loadSummary() {
    const url = elTitle?.dataset.summaryUrl;
    if (!url) return;

    const r = await fetch(url, { credentials: "same-origin" });
    if (!r.ok) throw new Error("No se pudo cargar summary");
    const data = await r.json();

    // Empresa
    if (elTitle) elTitle.textContent = data.empresa?.nombre || "Mi Empresa";

    // KPIs por carga (mes)
    const docs  = Number(data.kpis_carga?.docs || 0);
    const iva   = Number(data.kpis_carga?.iva || 0);
    const gasto = Number(data.kpis_carga?.gasto || 0);

    if (elDocs)  animateNumber(elDocs, docs);
    if (elIva)   animateNumber(elIva,  iva, { prefix: "$" });
    if (elGasto) animateNumber(elGasto, gasto, { prefix: "$" });
  }

  function buildItem(doc) {
    const li = document.createElement("li");
    li.className = "item";

    const tipo = doc.tipo_display || "Documento";
    const prov = doc.razon_social_proveedor || "";

    li.innerHTML = `
      <div class="left">
        <span class="dot dot-success" aria-hidden="true"><i class="fas fa-receipt"></i></span>
        <div class="info">
          <span class="title">${tipo}${prov ? ` de ${prov}` : ""}</span>
          <small class="meta">N° Folio: ${doc.folio || "-"}</small>
        </div>
      </div>
      <div class="right">
        <span class="tag tag-success">${doc.estado || "Procesado"}</span>
        <small class="when">${doc.fecha_emision || doc.creado_en || ""}</small>
        <div class="actions">
          <a href="/panel/documentos/" class="act">Ver</a>
          <a href="/panel/documentos/" class="act">Descargar</a>
          <a href="/panel/documentos/" class="act">Detalle</a>
        </div>
      </div>
    `;
    return li;
  }

  async function loadLatest() {
    const url = elTimeline?.dataset.latestUrl;
    if (!url) return;

    const r = await fetch(url, { credentials: "same-origin" });
    if (!r.ok) throw new Error("No se pudo cargar latest");
    const data = await r.json();

    // Limpia y pinta
    elTimeline.innerHTML = "";
    const results = Array.isArray(data.results) ? data.results : [];
    if (!results.length) {
      // Mostrar estado vacío
      cardsGrid?.setAttribute("data-state", "ready");
      elSkeleton?.setAttribute("hidden", "");
      const empty = document.querySelector(".card .empty");
      if (empty) empty.hidden = false;
      return;
    }

    results.forEach((doc) => elTimeline.appendChild(buildItem(doc)));

    // UI states
    cardsGrid?.setAttribute("data-state", "ready");
    elSkeleton?.setAttribute("hidden", "");
  }

  async function boot() {
    try {
      await Promise.all([loadSummary(), loadLatest()]);
    } catch (e) {
      console.error(e);
      // al menos saca el skeleton para no dejar “cargando” infinito
      cardsGrid?.setAttribute("data-state", "ready");
      elSkeleton?.setAttribute("hidden", "");
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot, { once: true });
  } else {
    boot();
  }
})();
