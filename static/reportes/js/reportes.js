document.addEventListener("DOMContentLoaded", function () {
  // --- ELEMENTOS DEL DOM ---
  const monthSelector = document.getElementById("monthSelector");
  const yearSelector = document.getElementById("yearSelector");
  const exportCsvBtn = document.getElementById("exportCsvBtn");
  const exportExcelBtn = document.getElementById("exportExcelBtn");
  const kpiIngresos = document.getElementById("kpiIngresos");
  const kpiGastos = document.getElementById("kpiGastos");
  const kpiResultado = document.getElementById("kpiResultado");
  const reportTableBody = document.getElementById("reportTableBody");
  const tblSkeleton = document.getElementById("tbl-skeleton");
  const tblEmpty = document.getElementById("tbl-empty");
  const chart1El = document.getElementById("ingresosVsGastosChart");
  const chart2El = document.getElementById("analisisIvaChart");

  // --- URLs DE LA API ---
  const kpiApiUrl = "/api/v1/panel/reportes/kpis/"; // La URL que me diste
  const docApiUrl = "/api/v1/documentos/"; // URL para la tabla (como en list.js)

  // --- INSTANCIAS DE GRÁFICOS (APEXCHARTS) ---
  let ingresosVsGastosChart, analisisIvaChart;
  let currentReportData = []; // Almacena los documentos actuales para exportar

  if (!monthSelector || !yearSelector || !reportTableBody) {
    console.error("Faltan elementos del DOM requeridos.");
    return;
  }

  // =================================================================
  // INICIALIZACIÓN DE GRÁFICOS
  // =================================================================

  function inicializarGraficos() {
    // --- Gráfico 1: Ingresos vs Gastos (Barra) ---
    const options1 = {
      series: [],
      chart: {
        type: "bar",
        height: 350,
        toolbar: { show: true },
      },
      plotOptions: {
        bar: {
          horizontal: false,
          columnWidth: "50%",
          dataLabels: { position: "top" },
        },
      },
      dataLabels: {
        enabled: true,
        formatter: (val) => formatCLP(val, false),
        offsetY: -20,
        style: {
          fontSize: "12px",
          colors: ["#304758"],
        },
      },
      xaxis: {
        categories: ["Periodo"], // Solo mostraremos una barra para el mes
      },
      yaxis: {
        title: { text: "Monto (CLP)" },
        labels: { formatter: (val) => formatCLP(val, true) },
      },
      colors: ["#0cac78", "#ef4444"], // Verde (Ingreso), Rojo (Gasto)
      noData: { text: "Cargando datos..." },
    };

    // --- Gráfico 2: Análisis de IVA (Dona) ---
    const options2 = {
      series: [],
      chart: {
        type: "donut",
        height: 350,
      },
      labels: ["IVA Crédito (Compras)", "IVA Débito (Ventas)"],
      legend: { position: "bottom" },
      tooltip: {
        y: { formatter: (val) => formatCLP(val, false) },
      },
      colors: ["#3b82f6", "#f59e0b"], // Azul, Naranja
      noData: { text: "Cargando datos..." },
    };

    if (chart1El) {
      chart1El.innerHTML = ""; // Limpiar skeleton
      ingresosVsGastosChart = new ApexCharts(chart1El, options1);
      ingresosVsGastosChart.render();
      chart1El.classList.add("loaded");
    }
    if (chart2El) {
      chart2El.innerHTML = ""; // Limpiar skeleton
      analisisIvaChart = new ApexCharts(chart2El, options2);
      analisisIvaChart.render();
      chart2El.classList.add("loaded");
    }
  }

  // =================================================================
  // LÓGICA DE DATOS PRINCIPAL
  // =================================================================

  /**
   * Rellena los selectores de Mes y Año.
   */
  function populateSelectors() {
    const now = new Date();
    const currentYear = now.getFullYear();
    const currentMonth = now.getMonth() + 1;

    for (let i = 0; i < 5; i++) {
      const year = currentYear - i;
      const option = new Option(year, year);
      yearSelector.add(option);
    }
    const months = [
      "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
      "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
    ];
    months.forEach((month, index) => {
      const option = new Option(month, index + 1);
      monthSelector.add(option);
    });

    monthSelector.value = currentMonth;
    yearSelector.value = currentYear;

    // Cargar datos al cambiar la selección
    monthSelector.addEventListener("change", loadDataForPeriod);
    yearSelector.addEventListener("change", loadDataForPeriod);
  }

  /**
   * Función maestra que se llama al cambiar la fecha.
   * Ejecuta ambas peticiones (KPIs y Tabla) en paralelo.
   */
  async function loadDataForPeriod() {
    // 1. Mostrar estado de carga en todos los componentes
    setKpiLoading();
    showTableLoading(true);
    ingresosVsGastosChart?.updateSeries([], false);
    analisisIvaChart?.updateSeries([], false);
    
    // Ejecutar ambas peticiones en paralelo
    await Promise.all([
        fetchKpiAndChartData(),
        fetchTableData()
    ]).catch(error => {
        console.error("Error al cargar datos del reporte:", error);
        // Mostrar error en la tabla
        if (tblSkeleton) tblSkeleton.hidden = true;
        if (tblEmpty) {
            tblEmpty.hidden = false;
            tblEmpty.querySelector(".empty-text").textContent = "Error al cargar el reporte.";
        }
    });
  }

  /**
   * 1. Busca los datos de KPIs y Gráficos (según tu nueva API).
   */
  async function fetchKpiAndChartData() {
    const month = monthSelector.value;
    const year = yearSelector.value;
    const apiUrl = `${kpiApiUrl}?mes=${month}&anio=${year}`;

    try {
      const response = await fetch(apiUrl, { headers: { Accept: "application/json" } });
      if (!response.ok) {
        throw new Error(`Error ${response.status} en API de KPIs`);
      }
      const data = await response.json();

      // --- RENDERIZAR DATOS (CORREGIDO) ---

      // 1. KPIs
      renderKpis(data.kpis);

      // 2. Gráfico Ingresos vs Gastos
      const ingGasData = data.ingresos_vs_gastos_chart;
      if (ingresosVsGastosChart && ingGasData) {
        ingresosVsGastosChart.updateSeries([
          { name: "Ingresos", data: [ingGasData.ingresos] },
          { name: "Gastos", data: [ingGasData.gastos] },
        ]);
      }

      // 3. Gráfico Análisis de IVA
      const ivaData = data.analisis_iva_chart;
      if (analisisIvaChart && ivaData) {
        analisisIvaChart.updateSeries([
          ivaData.iva_credito,
          ivaData.iva_debito,
        ]);
      }
      
      // (Aquí se podrían procesar los otros gráficos si tuvieras más contenedores HTML)

    } catch (error) {
      console.error("Error en fetchKpiAndChartData:", error);
      setKpiLoading(); // Resetear KPIs a '---' en caso de error
      // Lanzar el error para que Promise.all lo capture
      throw error;
    }
  }
  
  /**
   * 2. Busca los datos de la TABLA.
   */
  async function fetchTableData() {
    const month = monthSelector.value;
    const year = yearSelector.value;

    // Crear rango de fechas para el filtro
    const dateFrom = `${year}-${String(month).padStart(2, '0')}-01`;
    const lastDay = new Date(year, month, 0).getDate();
    const dateTo = `${year}-${String(month).padStart(2, '0')}-${lastDay}`;
    
    const params = new URLSearchParams();
    // Asumo que los filtros se llaman así (puedes necesitar ajustarlos)
    params.set('fecha_emision_after', dateFrom);
    params.set('fecha_emision_before', dateTo);
    // Podrías necesitar un filtro de estado, ej:
    // params.set('estado', 'procesado'); 
    
    const apiUrl = `${docApiUrl}?${params.toString()}`;

    try {
        const response = await fetch(apiUrl, { headers: { Accept: "application/json" } });
        if (!response.ok) {
            throw new Error(`Error ${response.status} en API de Documentos`);
        }
        const data = await response.json();
        
        // La API de documentos devuelve { "results": [...] }
        const documentos = data.results || [];
        
        renderTable(documentos);
        currentReportData = documentos; // Guardar para exportar

    } catch (error) {
        console.error("Error en fetchTableData:", error);
        showTableEmpty();
        if (tblEmpty) tblEmpty.querySelector(".empty-text").textContent = "Error al cargar documentos.";
        // Lanzar el error para que Promise.all lo capture
        throw error;
    }
  }


  /**
   * Pone los KPIs en estado "Cargando...".
   */
  function setKpiLoading() {
    const loadingText = "---";
    if (kpiIngresos) kpiIngresos.textContent = loadingText;
    if (kpiGastos) kpiGastos.textContent = loadingText;
    if (kpiResultado) {
      kpiResultado.textContent = loadingText;
      kpiResultado.classList.remove("positive", "negative");
    }
  }

  /**
   * Renderiza las tarjetas de KPI (CORREGIDO).
   */
  function renderKpis(kpis) {
    if (!kpis) {
        setKpiLoading();
        return;
    }
    
    // Corregido para usar las claves de tu JSON
    if (kpiIngresos) kpiIngresos.textContent = formatCLP(kpis.total_ingresos);
    if (kpiGastos) kpiGastos.textContent = formatCLP(kpis.total_gastos);
    if (kpiResultado) {
      // Corregido de 'resultado' a 'resultado_mes'
      const resultado = kpis.resultado_mes; 
      kpiResultado.textContent = formatCLP(resultado);
      kpiResultado.classList.toggle("positive", resultado >= 0);
      kpiResultado.classList.toggle("negative", resultado < 0);
    }
  }

  /**
   * Muestra el estado de carga en la tabla.
   */
  function showTableLoading(isLoading) {
    if (tblSkeleton) tblSkeleton.hidden = !isLoading;
    if (reportTableBody) reportTableBody.innerHTML = "";
    if (tblEmpty) tblEmpty.hidden = true;
  }

  /**
   * Muestra el estado vacío en la tabla.
   */
  function showTableEmpty() {
    if (reportTableBody) reportTableBody.innerHTML = "";
    if (tblSkeleton) tblSkeleton.hidden = true;
    if (tblEmpty) {
        tblEmpty.hidden = false;
        // Restaurar texto original
        tblEmpty.querySelector(".empty-text").textContent = "Sin datos para el periodo seleccionado.";
    }
  }

  /**
   * Renderiza la tabla de documentos.
   */
  function renderTable(documentos) {
    if (tblSkeleton) tblSkeleton.hidden = true;

    if (!documentos || documentos.length === 0) {
      showTableEmpty();
      return;
    }
    
    if (tblEmpty) tblEmpty.hidden = true;

    const html = documentos
      .map(
        (doc) => `
      <tr>
        <td>${doc.folio || "S/F"}</td>
        <td>${doc.tipo_documento || "No definido"}</td>
        <td>${formatDate(doc.fecha_emision)}</td>
        <td class="num">${formatCLP(doc.total)}</td>
      </tr>
    `
      )
      .join("");

    reportTableBody.innerHTML = html;
  }

  // =================================================================
  // UTILIDADES Y EXPORTACIÓN
  // =================================================================

  const formatCLP = (value, compact = false) => {
    if (value == null) return "—";
    const options = {
      style: "currency",
      currency: "CLP",
      maximumFractionDigits: 0,
    };
    if (compact) {
      options.notation = "compact";
      options.minimumFractionDigits = 0;
    }
    return new Intl.NumberFormat("es-CL", options).format(value);
  };

  const formatDate = (dateString) => {
    if (!dateString) return "—";
    try {
      // Asume que la fecha puede venir como 'YYYY-MM-DD' o ISO
      return new Date(dateString.split('T')[0]).toLocaleDateString("es-CL", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
      });
    } catch (e) {
      return dateString;
    }
  };

  // Lógica de exportación
  function getExportData() {
    if (currentReportData.length === 0) {
      alert("No hay documentos en la tabla para exportar. Genere un reporte primero.");
      return null;
    }
    // Simplificar datos para exportar
    return currentReportData.map(doc => ({
      Folio: doc.folio,
      Tipo: doc.tipo_documento,
      FechaEmision: formatDate(doc.fecha_emision),
      RUTProveedor: doc.rut_proveedor,
      Proveedor: doc.nombre_proveedor, // Asumo que este dato viene
      Neto: doc.monto_neto, // Asumo que este dato viene
      IVA: doc.iva, // Asumo que este dato viene
      Total: doc.total
    }));
  }
  
  function getFileName() {
    const month = monthSelector.options[monthSelector.selectedIndex].text;
    const year = yearSelector.value;
    return `Reporte_SGIDT_${month}_${year}`;
  }
  
  function downloadCSV(csvContent, fileName) {
      const blob = new Blob([`\uFEFF${csvContent}`], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = fileName;
      link.style.display = "none";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
  }

  if (exportCsvBtn) {
    exportCsvBtn.addEventListener("click", () => {
      const dataToExport = getExportData();
      if (!dataToExport) return;
      try {
        if (typeof XLSX === "undefined") throw new Error("XLSX no está cargado.");
        const ws = XLSX.utils.json_to_sheet(dataToExport);
        const csvOutput = XLSX.utils.sheet_to_csv(ws);
        downloadCSV(csvOutput, `${getFileName()}.csv`);
      } catch (err) {
        console.error(err);
        alert("No se pudo exportar a CSV: " + err.message);
      }
    });
  }

  if (exportExcelBtn) {
    exportExcelBtn.addEventListener("click", () => {
      const dataToExport = getExportData();
      if (!dataToExport) return;
      try {
        if (typeof XLSX === "undefined") throw new Error("XLSX no está cargado.");
        const ws = XLSX.utils.json_to_sheet(dataToExport);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "Reporte");
        XLSX.writeFile(wb, `${getFileName()}.xlsx`);
      } catch (err) {
        console.error(err);
        alert("No se pudo exportar a Excel: " + err.message);
      }
    });
  }

  // --- INICIALIZACIÓN ---
  populateSelectors();
  inicializarGraficos();
  loadDataForPeriod(); // Carga inicial
});