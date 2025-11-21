// static/panel/js/dashboard.js
(function () {
  const fmtCL = new Intl.NumberFormat("es-CL");
  const qs = (sel, root=document) => root.querySelector(sel);

  const elTitle   = qs("#db-title");
  const elDocs    = qs('[data-kpi="docs_mes"]');
  const elIva     = qs('[data-kpi="iva_mes"]');
  const elGasto   = qs('[data-kpi="gasto_mes"]');
  const elAlertas = qs('[data-kpi="alertas"]');
  const elAlertasPri = qs('[data-kpi="alertas_prioritarias"]');

  const elChart   = qs("#gastosChart");
  const elChartSk = qs(".chart-skeleton");

  const elRecent    = qs(".recent-list[data-latest-url]");
  const elRecentSk  = qs(".recent-list.skeleton");
  const elEmpty     = qs(".empty");

  // ---------- Animaciones KPI ----------
  const animate = (el, target, {prefix=""}={})=>{
    const start = performance.now(), dur=900, from=0;
    function tick(t){
      const p = Math.min((t-start)/dur,1);
      const v = Math.round(from + (target-from)*p);
      el.textContent = prefix + (prefix==="$" ? fmtCL.format(v) : v.toLocaleString("es-CL"));
      if(p<1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  };

  const setDelta = (key, val) => {
    const el = qs(`[data-kpi-delta="${key}"]`);
    if(!el) return;
    if(Number.isFinite(val)){
      el.textContent = `${val>=0?"+":""}${val.toFixed(1)}% desde el mes pasado`;
      el.style.color = val>=0 ? "#15803d" : "#b91c1c";
      el.hidden = false;
    }else{
      el.hidden = true;
    }
  };

  async function loadSummary(){
    const url = elTitle?.dataset.summaryUrl;
    if(!url) return;

    const r = await fetch(url, {credentials:"same-origin"});
    if(!r.ok) throw new Error("summary failed");
    const data = await r.json();

    if(elTitle) elTitle.textContent = data.empresa?.nombre || "Mi Empresa";

    const docs  = Number(data.kpis_carga?.docs ?? 0);
    const iva   = Number(data.kpis_carga?.iva ?? 0);
    const gasto = Number(data.kpis_carga?.gasto ?? 0);
    const alert = Number(data.alertas?.total ?? 0);
    const alertPri = Number(data.alertas?.prioritarias ?? 0);

    if(elDocs)  animate(elDocs, docs);
    if(elIva)   animate(elIva, iva,   {prefix:"$"});
    if(elGasto) animate(elGasto, gasto,{prefix:"$"});
    if(elAlertas) elAlertas.textContent = alert.toLocaleString("es-CL");
    if(elAlertasPri) elAlertasPri.textContent = alertPri.toLocaleString("es-CL");

    setDelta("docs_mes",  Number(data.kpis_carga?.delta_docs ?? NaN));
    setDelta("iva_mes",   Number(data.kpis_carga?.delta_iva ?? NaN));
    setDelta("gasto_mes", Number(data.kpis_carga?.delta_gasto ?? NaN));
  }

  // ---------- Chart: ApexCharts ----------
  async function loadChart(){
    const elChart = document.getElementById("gastosChart");
    const elSk = document.querySelector(".chart-skeleton");
    if(!elChart) return;

    const url = elChart.dataset.chartUrl;
    if(!url) return;

    try{
      const r = await fetch(url, { credentials: "same-origin" });
      if(!r.ok) throw new Error(`HTTP ${r.status}`);

      const data = await r.json(); 
      const labels = Array.isArray(data) ? data.map(d=>String(d.label||"")) : [];
      const values = Array.isArray(data) ? data.map(d=>Number(d.total||0)) : [];

      if(!labels.length){
        elSk?.remove();
        elChart.innerHTML = `<div style="padding:12px;color:#6b7280">Sin datos para los últimos 6 meses.</div>`;
        return;
      }

      const options = {
        chart: { type: 'bar', height: 300, toolbar: { show:false } },
        series: [{ name: 'Gastos', data: values }],
        xaxis: { categories: labels, axisBorder:{show:false}, axisTicks:{show:false} },
        yaxis: { labels: { formatter: v => "$" + new Intl.NumberFormat("es-CL").format(Math.round(v)) } },
        grid: { borderColor: '#eef2f7' },
        plotOptions: { bar: { borderRadius: 6, columnWidth: '45%' } },
        dataLabels: { enabled: false },
        tooltip: { y: { formatter: val => "$" + new Intl.NumberFormat("es-CL").format(Math.round(val)) } },
        colors: ['#111827']
      };

      const chart = new ApexCharts(elChart, options);
      await chart.render();
      elSk?.remove();

    } catch (err) {
      console.error("[gastos6m] error:", err);
      elSk?.remove();
      elChart.innerHTML = `<div style="padding:12px;color:#b91c1c">Error al cargar gráfico.</div>`;
    }
  }


  // ---------- Formateo de Fechas (MEJORADO) ----------
  const formatDate = (iso) => {
    if(!iso) return "—";
    const d = new Date(iso);
    // Validar si la fecha es correcta
    if(isNaN(d.getTime())) return "—";
    
    // Retorna formato dd/mm/yyyy (ej: 21/11/2025)
    return d.toLocaleDateString("es-CL", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric"
    });
  };

  function badge(estado){
    const s = (estado||"").toLowerCase();
    if(s.includes("apro") || s==="procesado") return '<span class="badge ok">Aprobado</span>';
    if(s.includes("pend")) return '<span class="badge warn">Pendiente</span>';
    if(s.includes("rech")) return '<span class="badge err">Rechazado</span>';
    return '<span class="badge warn">-</span>';
  }

  function buildRecentItem(d){
    const li = document.createElement("li"); li.className="recent-item";
    const prov = d.razon_social_proveedor || d.proveedor || "";
    const folio = d.folio || "-";
    const monto = (d.total!=null) ? "$"+fmtCL.format(Number(d.total)) : "";
    
    // Busca la fecha en varios campos posibles para evitar NaN
    const rawDate = d.fecha_emision || d.created_at || d.creado_en || d.fecha;
    const dateStr = formatDate(rawDate);

    li.innerHTML = `
      <div class="recent-left">
        <div class="rec-title">F-${folio} ${badge(d.estado)}</div>
        <div class="rec-sub">${prov || "Documento tributario"}</div>
      </div>
      <div class="recent-right">
        <strong class="rec-amount">${monto}</strong>
        <small class="text-muted">${dateStr}</small>
      </div>
    `;
    return li;
  }

  async function loadRecent(){
    const url = elRecent?.dataset.latestUrl;
    if(!url) return;

    // 1. Ocultar "Vacío" forzosamente antes de cargar
    if(elEmpty) {
        elEmpty.hidden = true;
        elEmpty.style.display = 'none'; 
    }

    try {
        const r = await fetch(url, {credentials:"same-origin"});
        if(!r.ok) throw new Error("latest failed");
        const data = await r.json();
        const results = Array.isArray(data.results) ? data.results : [];
        
        elRecent.innerHTML = "";

        // 2. Si NO hay resultados, mostrar "Vacío"
        if(!results.length){
            if(elEmpty) {
                elEmpty.hidden = false;
                elEmpty.style.display = ''; // Restaurar display original (flex/block)
            }
            elRecentSk?.remove();
            return;
        }

        // 3. Si HAY resultados, asegurar que "Vacío" siga oculto
        if(elEmpty) {
            elEmpty.hidden = true;
            elEmpty.style.display = 'none'; 
        }

        results.forEach(d=>elRecent.appendChild(buildRecentItem(d)));
        elRecentSk?.remove();

    } catch(e) {
        console.error(e);
        elRecentSk?.remove();
        // Opcional: mostrar mensaje de error si falla la carga
    }
  }

  async function boot(){
    await Promise.all([loadSummary(), loadChart(), loadRecent()]);
  }

  if(document.readyState==="loading") document.addEventListener("DOMContentLoaded", boot, {once:true});
  else boot();
})();