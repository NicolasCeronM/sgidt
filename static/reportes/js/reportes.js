document.addEventListener('DOMContentLoaded', function () {

    // --- ELEMENTOS DEL DOM ---
    const monthSelector = document.getElementById('monthSelector');
    const yearSelector = document.getElementById('yearSelector');
    const exportCsvBtn = document.getElementById('exportCsvBtn');
    const exportExcelBtn = document.getElementById('exportExcelBtn');
    const kpiIngresos = document.getElementById('kpiIngresos');
    const kpiGastos = document.getElementById('kpiGastos');
    const kpiResultado = document.getElementById('kpiResultado');
    const reportTableBody = document.getElementById('reportTableBody');

    // --- INSTANCIAS DE GRÁFICOS (APEXCHARTS) ---
    let ingresosVsGastosChart, analisisIvaChart, distribucionIngresosChart, distribucionGastosChart;

    /**
     * Inicializa todos los gráficos con una configuración base.
     */
    function inicializarGraficos() {
        // Opciones comunes para los gráficos de dona/pastel
        const commonPieOptions = {
            chart: { type: 'donut', height: 350 },
            legend: { position: 'bottom' },
            responsive: [{
                breakpoint: 480,
                options: {
                    chart: { width: 250 },
                    legend: { position: 'bottom' }
                }
            }]
        };

        // 1. Gráfico de Ingresos vs Gastos (Barras)
        const ingresosVsGastosOptions = {
            series: [],
            chart: { type: 'bar', height: 350 },
            plotOptions: { bar: { horizontal: false, columnWidth: '55%' } },
            dataLabels: { enabled: false },
            stroke: { show: true, width: 2, colors: ['transparent'] },
            xaxis: { categories: ['Resumen del Mes'] },
            yaxis: { title: { text: '$ (CLP)' } },
            fill: { opacity: 1 },
            tooltip: { y: { formatter: (val) => `$${new Intl.NumberFormat('es-CL').format(val)}` } },
            noData: { text: 'Cargando datos...' }
        };
        ingresosVsGastosChart = new ApexCharts(document.querySelector("#ingresosVsGastosChart"), ingresosVsGastosOptions);
        ingresosVsGastosChart.render();
        
        // 2. Gráfico de Análisis de IVA (Dona)
        const analisisIvaOptions = { ...commonPieOptions, series: [], labels: [], noData: { text: 'Cargando datos...' } };
        analisisIvaChart = new ApexCharts(document.querySelector("#analisisIvaChart"), analisisIvaOptions);
        analisisIvaChart.render();

        // 3. Gráfico de Distribución de Ingresos (Pastel)
        const distribucionIngresosOptions = { ...commonPieOptions, chart: {...commonPieOptions.chart, type: 'pie'}, series: [], labels: [], noData: { text: 'Cargando datos...' } };
        distribucionIngresosChart = new ApexCharts(document.querySelector("#distribucionIngresosChart"), distribucionIngresosOptions);
        distribucionIngresosChart.render();
        
        // 4. Gráfico de Distribución de Gastos (Pastel)
        const distribucionGastosOptions = { ...commonPieOptions, chart: {...commonPieOptions.chart, type: 'pie'}, series: [], labels: [], noData: { text: 'Cargando datos...' } };
        distribucionGastosChart = new ApexCharts(document.querySelector("#distribucionGastosChart"), distribucionGastosOptions);
        distribucionGastosChart.render();
    }


    // --- LÓGICA DE ACTUALIZACIÓN DE GRÁFICOS ---
    function actualizarGraficos(chartData) {
        // 1. Actualizar Ingresos vs Gastos
        ingresosVsGastosChart.updateSeries([
            { name: 'Ingresos', data: [chartData.ingresos_gastos.ingresos] },
            { name: 'Gastos', data: [chartData.ingresos_gastos.gastos] }
        ]);

        // 2. Actualizar Análisis de IVA
        analisisIvaChart.updateOptions({
            series: [chartData.analisis_iva.iva_credito, chartData.analisis_iva.iva_debito],
            labels: ['IVA Crédito (Gastos)', 'IVA Débito (Ingresos)']
        });
        
        // 3. Actualizar Distribución de Ingresos
        distribucionIngresosChart.updateOptions({
            series: Object.values(chartData.distribucion_ingresos),
            labels: Object.keys(chartData.distribucion_ingresos)
        });

        // 4. Actualizar Distribución de Gastos
        distribucionGastosChart.updateOptions({
            series: Object.values(chartData.distribucion_gastos),
            labels: Object.keys(chartData.distribucion_gastos)
        });
    }

    // --- LÓGICA GENERAL (Filtros, AJAX, etc.) ---
    function inicializarFiltros() {
        const meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"];
        const fechaActual = new Date();
        const mesActual = fechaActual.getMonth();
        const añoActual = fechaActual.getFullYear();
        meses.forEach((mes, index) => {
            const option = new Option(mes, index + 1);
            option.selected = (index === mesActual);
            monthSelector.add(option);
        });
        for (let i = 0; i < 5; i++) {
            const año = añoActual - i;
            const option = new Option(año, año);
            option.selected = (año === añoActual);
            yearSelector.add(option);
        }
    }

    function formatCurrency(valor) {
        return `$${new Intl.NumberFormat('es-CL').format(valor || 0)}`;
    }

    async function cargarDatosReporte() {
        const month = monthSelector.value;
        const year = yearSelector.value;
        try {
            const response = await fetch(`?month=${month}&year=${year}`, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            if (!response.ok) throw new Error('La respuesta del servidor no fue exitosa.');
            const data = await response.json();
            actualizarUI(data);
        } catch (error) {
            console.error("Error al cargar los datos del reporte:", error);
        }
    }

    function actualizarUI(data) {
        actualizarKPIs(data.kpis);
        actualizarTabla(data.ultimos_documentos);
        actualizarGraficos(data.charts);
    }

    function actualizarKPIs(kpis) {
        kpiIngresos.textContent = formatCurrency(kpis.total_ingresos);
        kpiGastos.textContent = formatCurrency(kpis.total_gastos);
        kpiResultado.textContent = formatCurrency(kpis.resultado_mes);
    }

    function actualizarTabla(documentos) {
        reportTableBody.innerHTML = '';
        if (documentos.length === 0) {
            reportTableBody.innerHTML = '<tr><td colspan="4" class="text-center">No hay documentos para el período seleccionado.</td></tr>';
            return;
        }
        documentos.forEach(doc => {
            const row = `
                <tr>
                    <td>${doc.folio || 'N/A'}</td>
                    <td>${doc.tipo_documento_display}</td>
                    <td>${doc.fecha_emision}</td>
                    <td>${formatCurrency(doc.monto_total)}</td>
                </tr>`;
            reportTableBody.innerHTML += row;
        });
    }

    // --- MANEJADORES DE EVENTOS ---
    monthSelector.addEventListener('change', cargarDatosReporte);
    yearSelector.addEventListener('change', cargarDatosReporte);
    exportCsvBtn.addEventListener('click', () => {
        window.location.href = `/panel/reportes/exportar/?month=${monthSelector.value}&year=${yearSelector.value}&file_type=csv`;
    });
    exportExcelBtn.addEventListener('click', () => {
        window.location.href = `/panel/reportes/exportar/?month=${monthSelector.value}&year=${yearSelector.value}&file_type=excel`;
    });

    // --- INICIALIZACIÓN ---
    inicializarFiltros();
    inicializarGraficos(); // Inicia los gráficos con estructura vacía
    cargarDatosReporte(); // Busca los datos y los carga en los gráficos
});