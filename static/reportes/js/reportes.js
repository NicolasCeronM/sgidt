document.addEventListener('DOMContentLoaded', function () {

    // --- ELEMENTOS DEL DOM (guardas por si alguno falta) ---
    const monthSelector = document.getElementById('monthSelector');
    const yearSelector = document.getElementById('yearSelector');
    const exportCsvBtn = document.getElementById('exportCsvBtn');
    const exportExcelBtn = document.getElementById('exportExcelBtn');
    const kpiIngresos = document.getElementById('kpiIngresos');
    const kpiGastos = document.getElementById('kpiGastos');
    const kpiResultado = document.getElementById('kpiResultado');
    const reportTableBody = document.getElementById('reportTableBody');

    if (!monthSelector || !yearSelector || !reportTableBody) {
        console.error('Faltan elementos del DOM requeridos (monthSelector, yearSelector o reportTableBody).');
        return;
    }

    // --- INSTANCIAS DE GRÁFICOS (APEXCHARTS) ---
    let ingresosVsGastosChart, analisisIvaChart, distribucionIngresosChart, distribucionGastosChart;

    // Almacena los documentos actuales para exportar
    let currentReportData = [];

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
            tooltip: { y: { formatter: (val) => `$${new Intl.NumberFormat('es-CL').format(val || 0)}` } },
            noData: { text: 'Cargando datos...' }
        };
        if (document.querySelector("#ingresosVsGastosChart")) {
            ingresosVsGastosChart = new ApexCharts(document.querySelector("#ingresosVsGastosChart"), ingresosVsGastosOptions);
            ingresosVsGastosChart.render();
        }

        // 2. Gráfico de Análisis de IVA (Dona)
        const analisisIvaOptions = { ...commonPieOptions, series: [], labels: [], noData: { text: 'Cargando datos...' } };
        if (document.querySelector("#analisisIvaChart")) {
            analisisIvaChart = new ApexCharts(document.querySelector("#analisisIvaChart"), analisisIvaOptions);
            analisisIvaChart.render();
        }

        // 3. Gráfico de Distribución de Ingresos (Pastel)
        const distribucionIngresosOptions = { ...commonPieOptions, chart: { ...commonPieOptions.chart, type: 'pie' }, series: [], labels: [], noData: { text: 'Cargando datos...' } };
        if (document.querySelector("#distribucionIngresosChart")) {
            distribucionIngresosChart = new ApexCharts(document.querySelector("#distribucionIngresosChart"), distribucionIngresosOptions);
            distribucionIngresosChart.render();
        }

        // 4. Gráfico de Distribución de Gastos (Pastel)
        const distribucionGastosOptions = { ...commonPieOptions, chart: { ...commonPieOptions.chart, type: 'pie' }, series: [], labels: [], noData: { text: 'Cargando datos...' } };
        if (document.querySelector("#distribucionGastosChart")) {
            distribucionGastosChart = new ApexCharts(document.querySelector("#distribucionGastosChart"), distribucionGastosOptions);
            distribucionGastosChart.render();
        }
    }


    // --- LÓGICA DE ACTUALIZACIÓN DE GRÁFICOS ---
    function actualizarGraficos(chartData = {}) {
        if (!chartData) return;

        // 1. Actualizar Ingresos vs Gastos
        if (ingresosVsGastosChart && chartData.ingresos_gastos) {
            ingresosVsGastosChart.updateSeries([
                { name: 'Ingresos', data: [chartData.ingresos_gastos.ingresos || 0] },
                { name: 'Gastos', data: [chartData.ingresos_gastos.gastos || 0] }
            ]);
        }

        // 2. Actualizar Análisis de IVA
        if (analisisIvaChart && chartData.analisis_iva) {
            analisisIvaChart.updateOptions({
                series: [chartData.analisis_iva.iva_credito || 0, chartData.analisis_iva.iva_debito || 0],
                labels: ['IVA Crédito (Gastos)', 'IVA Débito (Ingresos)']
            });
        }

        // 3. Actualizar Distribución de Ingresos
        if (distribucionIngresosChart && chartData.distribucion_ingresos) {
            distribucionIngresosChart.updateOptions({
                series: Object.values(chartData.distribucion_ingresos || {}),
                labels: Object.keys(chartData.distribucion_ingresos || {})
            });
        }

        // 4. Actualizar Distribución de Gastos
        if (distribucionGastosChart && chartData.distribucion_gastos) {
            distribucionGastosChart.updateOptions({
                series: Object.values(chartData.distribucion_gastos || {}),
                labels: Object.keys(chartData.distribucion_gastos || {})
            });
        }
    }

    // --- LÓGICA GENERAL (Filtros, AJAX, etc.) ---
    function inicializarFiltros() {
        const meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"];
        const fechaActual = new Date();
        const mesActual = fechaActual.getMonth();
        const añoActual = fechaActual.getFullYear();

        // Limpiar opciones previas (por si se re-ejecuta)
        monthSelector.innerHTML = '';
        yearSelector.innerHTML = '';

        meses.forEach((mes, index) => {
            const option = new Option(mes, index + 1);
            if (index === mesActual) option.selected = true;
            monthSelector.add(option);
        });
        for (let i = 0; i < 5; i++) {
            const año = añoActual - i;
            const option = new Option(año, año);
            if (año === añoActual) option.selected = true;
            yearSelector.add(option);
        }
    }

    function formatCurrency(valor) {
        return `$${new Intl.NumberFormat('es-CL').format(valor || 0)}`;
    }

    async function cargarDatosReporte() {
        const month = monthSelector.value;
        const year = yearSelector.value;

        reportTableBody.innerHTML = '<tr><td colspan="4" class="table-loading">Cargando datos...</td></tr>';

        try {
            const response = await fetch(`?month=${encodeURIComponent(month)}&year=${encodeURIComponent(year)}`, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            if (!response.ok) throw new Error('La respuesta del servidor no fue exitosa.');
            const data = await response.json();

            // Guardamos los documentos para exportación y uso posterior
            currentReportData = data.ultimos_documentos || [];

            actualizarUI(data);
        } catch (error) {
            console.error("Error al cargar los datos del reporte:", error);
            reportTableBody.innerHTML = '<tr><td colspan="4" class="table-loading">Error al cargar datos.</td></tr>';
            currentReportData = []; // Limpiar datos en caso de error
            // también podemos limpiar KPIs
            if (kpiIngresos) kpiIngresos.textContent = formatCurrency(0);
            if (kpiGastos) kpiGastos.textContent = formatCurrency(0);
            if (kpiResultado) kpiResultado.textContent = formatCurrency(0);
        }
    }

    function actualizarUI(data = {}) {
        actualizarKPIs(data.kpis || {});
        actualizarTabla(data.ultimos_documentos || []);
        actualizarGraficos(data.charts || {});
    }

    function actualizarKPIs(kpis = {}) {
        if (kpiIngresos) kpiIngresos.textContent = formatCurrency(kpis.total_ingresos || 0);
        if (kpiGastos) kpiGastos.textContent = formatCurrency(kpis.total_gastos || 0);
        if (kpiResultado) kpiResultado.textContent = formatCurrency(kpis.resultado_mes || 0);
    }

    function actualizarTabla(documentos = []) {
        reportTableBody.innerHTML = '';

        if (!documentos || documentos.length === 0) {
            reportTableBody.innerHTML = '<tr><td colspan="4" class="table-loading">No hay documentos para el período seleccionado.</td></tr>';
            return;
        }

        // Construir filas de forma segura (evitar innerHTML repetido por rendimiento)
        const fragment = document.createDocumentFragment();
        documentos.forEach(doc => {
            const tr = document.createElement('tr');

            const tdFolio = document.createElement('td');
            tdFolio.textContent = doc.folio || 'N/A';
            tr.appendChild(tdFolio);

            const tdTipo = document.createElement('td');
            tdTipo.textContent = doc.tipo_documento_display || '';
            tr.appendChild(tdTipo);

            const tdFecha = document.createElement('td');
            tdFecha.textContent = doc.fecha_emision || '';
            tr.appendChild(tdFecha);

            const tdMonto = document.createElement('td');
            tdMonto.textContent = formatCurrency(doc.monto_total || 0);
            tr.appendChild(tdMonto);

            fragment.appendChild(tr);
        });
        reportTableBody.appendChild(fragment);
    }

    // --- (AÑADIDO) LÓGICA DE EXPORTACIÓN ---

    /**
     * Prepara los datos para la exportación.
     */
    function getExportData() {
        if (!currentReportData || currentReportData.length === 0) {
            alert("No hay documentos para exportar. Por favor, cargue un reporte primero.");
            return null;
        }

        // Mapea los datos. Exportamos el valor numérico (doc.monto_total).
        return currentReportData.map(doc => ({
            "Folio": doc.folio || 'N/A',
            "Tipo de Documento": doc.tipo_documento_display || '',
            "Fecha de Emisión": doc.fecha_emision || '',
            "Monto Total": doc.monto_total != null ? doc.monto_total : ''
        }));
    }

    /**
     * Función auxiliar para descargar el archivo CSV con codificación UTF-8.
     */
    function downloadCSV(csvContent, fileName) {
        const a = document.createElement('a');
        const blob = new Blob(["\uFEFF" + csvContent], { type: 'text/csv;charset=utf-8;' });
        a.href = URL.createObjectURL(blob);
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(a.href);
    }

    /**
     * Obtiene un nombre de archivo dinámico basado en los filtros.
     */
    function getFileName() {
        try {
            const monthText = monthSelector.options[monthSelector.selectedIndex].text.toLowerCase();
            const year = yearSelector.value;
            return `reporte_${monthText}_${year}`;
        } catch (e) {
            return 'reporte_sgidt';
        }
    }

    // --- MANEJADORES DE EVENTOS ---
    monthSelector.addEventListener('change', cargarDatosReporte);
    yearSelector.addEventListener('change', cargarDatosReporte);

    if (exportCsvBtn) {
        exportCsvBtn.addEventListener('click', () => {
            const dataToExport = getExportData();
            if (!dataToExport) return; // Salir si no hay datos

            try {
                if (typeof XLSX === 'undefined') throw new Error('XLSX no está cargado. Asegúrate de incluir la librería SheetJS (xlsx).');

                const ws = XLSX.utils.json_to_sheet(dataToExport);
                const csvOutput = XLSX.utils.sheet_to_csv(ws);

                downloadCSV(csvOutput, `${getFileName()}.csv`);
            } catch (err) {
                console.error(err);
                alert('No se pudo exportar a CSV: ' + err.message);
            }
        });
    }

    if (exportExcelBtn) {
        exportExcelBtn.addEventListener('click', () => {
            const dataToExport = getExportData();
            if (!dataToExport) return; // Salir si no hay datos

            try {
                if (typeof XLSX === 'undefined') throw new Error('XLSX no está cargado. Asegúrate de incluir la librería SheetJS (xlsx).');

                const ws = XLSX.utils.json_to_sheet(dataToExport);
                const wb = XLSX.utils.book_new();
                XLSX.utils.book_append_sheet(wb, ws, 'Reporte');

                XLSX.writeFile(wb, `${getFileName()}.xlsx`);
            } catch (err) {
                console.error(err);
                alert('No se pudo exportar a Excel: ' + err.message);
            }
        });
    }

    // --- INICIALIZACIÓN ---
    inicializarFiltros();
    inicializarGraficos(); // Inicia los gráficos con estructura vacía
    cargarDatosReporte(); // Busca los datos y los carga en los gráficos
});
