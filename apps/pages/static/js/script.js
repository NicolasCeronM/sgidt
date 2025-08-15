// ==== Estado simulado (mock) ====
let documentsData = [];
let reportData = [];

// ==== Boot ====
document.addEventListener("DOMContentLoaded", () => {
  loadMockData();
  setupNavActiveLink();
  setupEventListeners();

  // Renderizaciones condicionales según elementos presentes en la página
  renderChart();        // gráfico principal (si existe #expenseChart)
  renderMiniCharts();   // mini charts en cards (si existen)
  animateCounters();    // contadores animados (si existen)

  // Relleno de tablas si estás en esas páginas
  loadDocuments();
  loadReports();
});

// ==== Navbar: marcar enlace activo por URL ====
function setupNavActiveLink() {
  const here = location.pathname.replace(/\/+$/, "");
  document.querySelectorAll(".nav-link").forEach((a) => {
    const href = (a.getAttribute("href") || "").replace(/\/+$/, "");
    if (href && (here === href || (href === "" && (here === "" || here === "/")))) {
      a.classList.add("active");
    }
  });
}

// ==== Listeners globales (reutilizable en todas las páginas) ====
function setupEventListeners() {
  // Menú móvil
  const hamburger = document.querySelector(".hamburger");
  const navMenu = document.querySelector(".nav-menu");
  if (hamburger && navMenu) {
    hamburger.addEventListener("click", () => {
      navMenu.classList.toggle("active");
    });
  }

  // Upload de archivos (página Documentos)
  const fileInput = document.getElementById("fileInput");
  const uploadArea = document.getElementById("uploadArea");
  if (fileInput && uploadArea) {
    fileInput.addEventListener("change", handleFileUpload);

    uploadArea.addEventListener("dragover", (e) => {
      e.preventDefault();
      uploadArea.classList.add("dragover");
    });
    uploadArea.addEventListener("dragleave", () => uploadArea.classList.remove("dragover"));
    uploadArea.addEventListener("drop", (e) => {
      e.preventDefault();
      uploadArea.classList.remove("dragover");
      handleFiles(e.dataTransfer.files);
    });
    uploadArea.addEventListener("click", () => fileInput.click());
  }

  // Filtros/periodos en reportes
  const reportPeriod = document.getElementById("reportPeriod");
  if (reportPeriod) {
    reportPeriod.addEventListener("change", updateReportData);
  }

  // Selector de periodo del gráfico principal del home
  const chartPeriod = document.getElementById("chartPeriod");
  if (chartPeriod) {
    chartPeriod.addEventListener("change", (e) => {
      const txt = e.target.options[e.target.selectedIndex].text;
      showNotification(`Actualizando gráfico para período: ${txt}`, "info");
      setTimeout(() => {
        renderChart();
        showNotification("Gráfico actualizado", "success");
      }, 800);
    });
  }

  // Filtros de actividad (home)
  setupActivityFilters();
}

// ==== Datos Mock ====
function loadMockData() {
  documentsData = [
    { date: "2024-01-15", type: "factura",     folio: "12345", rut: "12.345.678-9", amount: 150000,  status: "validado" },
    { date: "2024-01-14", type: "boleta",      folio: "67890", rut: "98.765.432-1", amount: 75000,   status: "pendiente" },
    { date: "2024-01-13", type: "factura",     folio: "11111", rut: "11.111.111-1", amount: 200000,  status: "error" },
    { date: "2024-01-12", type: "nota-credito",folio: "22222", rut: "22.222.222-2", amount: 50000,   status: "validado" },
    { date: "2024-01-11", type: "boleta",      folio: "33333", rut: "33.333.333-3", amount: 125000,  status: "validado" },
  ];

  reportData = [
    { month: "Enero 2024",   income: 4567890, expenses: 3245678, ivaDebit: 867991,  ivaCredit: 616787,  result: 1322212 },
    { month: "Febrero 2024", income: 5234567, expenses: 3876543, ivaDebit: 994569,  ivaCredit: 736543,  result: 1358024 },
    { month: "Marzo 2024",   income: 4876543, expenses: 3334567, ivaDebit: 926543,  ivaCredit: 633567,  result: 1541976 },
  ];
}

// ==== Gráfico principal (canvas 2D "casero") ====
function renderChart() {
  const canvas = document.getElementById("expenseChart");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  const width  = (canvas.width  = canvas.offsetWidth || 600);
  const height = (canvas.height = 300);

  const categories = ["Servicios", "Materiales", "Personal", "Marketing", "Otros"];
  const values     = [3500000, 2800000, 4200000, 1500000, 2000000];
  const colors     = ["#10b981", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6"];

  const gradients = colors.map((color) => {
    const g = ctx.createLinearGradient(0, 0, 0, height);
    g.addColorStop(0, color);
    g.addColorStop(1, color + "80"); // alpha
    return g;
  });

  const maxValue = Math.max(...values);
  const barWidth   = (width / categories.length) * 0.7;
  const barSpacing = (width / categories.length) * 0.3;

  ctx.clearRect(0, 0, width, height);

  // grid suave
  ctx.strokeStyle = "#f1f5f9";
  ctx.lineWidth = 1;
  for (let i = 1; i <= 5; i++) {
    const y = (height - 60) * (i / 5) + 20;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(width, y);
    ctx.stroke();
  }

  categories.forEach((category, index) => {
    const barHeight = (values[index] / maxValue) * (height - 80);
    const x = index * (barWidth + barSpacing) + barSpacing / 2;
    const y = height - barHeight - 50;

    // barra con esquinas redondeadas
    ctx.fillStyle = gradients[index];
    ctx.beginPath();
    if (ctx.roundRect) {
      ctx.roundRect(x, y, barWidth, barHeight, 8);
    } else {
      // fallback simple
      ctx.rect(x, y, barWidth, barHeight);
    }
    ctx.fill();

    // etiqueta categoría
    ctx.fillStyle = "#374151";
    ctx.font = "600 12px Inter";
    ctx.textAlign = "center";
    ctx.fillText(category, x + barWidth / 2, height - 25);

    // etiqueta valor
    ctx.fillStyle = "#6b7280";
    ctx.font = "500 10px Inter";
    ctx.fillText(formatCurrency(values[index]), x + barWidth / 2, y - 8);
  });
}

// ==== Documentos (tabla) ====
function loadDocuments() {
  const tbody = document.getElementById("documentsTableBody");
  if (!tbody) return;

  tbody.innerHTML = "";
  documentsData.forEach((doc) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${formatDate(doc.date)}</td>
      <td>${capitalizeFirst(doc.type)}</td>
      <td>${doc.folio}</td>
      <td>${doc.rut}</td>
      <td>${formatCurrency(doc.amount)}</td>
      <td><span class="status-badge ${doc.status}">${capitalizeFirst(doc.status)}</span></td>
      <td>
        <button class="btn btn-small btn-secondary" data-folio="${doc.folio}">
          <i class="fas fa-eye"></i> Ver
        </button>
      </td>`;
    tbody.appendChild(row);
  });

  // Delegación para botones "Ver"
  tbody.addEventListener("click", (e) => {
    const btn = e.target.closest("button[data-folio]");
    if (!btn) return;
    previewDocument(btn.getAttribute("data-folio"));
  });
}

function handleFileUpload(event) {
  handleFiles(event.target.files);
}
function handleFiles(files) {
  Array.from(files).forEach((file) => validateFile(file) && uploadFile(file));
}
function validateFile(file) {
  const allowed = ["application/pdf", "image/jpeg", "image/jpg", "image/png"];
  const maxSize = 10 * 1024 * 1024; // 10MB
  if (!allowed.includes(file.type)) { showNotification("Tipo de archivo no permitido", "error"); return false; }
  if (file.size > maxSize)         { showNotification("El archivo es demasiado grande (máx. 10MB)", "error"); return false; }
  return true;
}
function uploadFile(file) {
  showNotification("Subiendo archivo...", "info");
  setTimeout(() => {
    const newDoc = {
      date: new Date().toISOString().split("T")[0],
      type: "factura",
      folio: Math.floor(Math.random() * 100000).toString(),
      rut: "12.345.678-9",
      amount: Math.floor(Math.random() * 1_000_000),
      status: "pendiente",
    };
    documentsData.unshift(newDoc);
    loadDocuments();
    showNotification("Archivo subido exitosamente", "success");
  }, 1200);
}
function previewDocument(folio) {
  showNotification(`Previsualizando documento ${folio}`, "info");
}

// filtros en documentos
function applyFilters() {
  const dateFrom  = document.getElementById("dateFrom")?.value || "";
  const dateTo    = document.getElementById("dateTo")?.value || "";
  const docType   = document.getElementById("docType")?.value || "";
  const docStatus = document.getElementById("docStatus")?.value || "";

  let filtered = [...documentsData];
  if (dateFrom)  filtered = filtered.filter((d) => d.date >= dateFrom);
  if (dateTo)    filtered = filtered.filter((d) => d.date <= dateTo);
  if (docType)   filtered = filtered.filter((d) => d.type === docType);
  if (docStatus) filtered = filtered.filter((d) => d.status === docStatus);

  const tbody = document.getElementById("documentsTableBody");
  if (!tbody) return;
  tbody.innerHTML = "";
  filtered.forEach((doc) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${formatDate(doc.date)}</td>
      <td>${capitalizeFirst(doc.type)}</td>
      <td>${doc.folio}</td>
      <td>${doc.rut}</td>
      <td>${formatCurrency(doc.amount)}</td>
      <td><span class="status-badge ${doc.status}">${capitalizeFirst(doc.status)}</span></td>
      <td><button class="btn btn-small btn-secondary" data-folio="${doc.folio}">
        <i class="fas fa-eye"></i> Ver
      </button></td>`;
    tbody.appendChild(row);
  });
  showNotification(`Filtros aplicados. ${filtered.length} documentos encontrados`, "success");
}

// ==== Reportes ====
function loadReports() {
  const tbody = document.getElementById("reportTableBody");
  if (!tbody) return;

  tbody.innerHTML = "";
  reportData.forEach((r) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${r.month}</td>
      <td>${formatCurrency(r.income)}</td>
      <td>${formatCurrency(r.expenses)}</td>
      <td>${formatCurrency(r.ivaDebit)}</td>
      <td>${formatCurrency(r.ivaCredit)}</td>
      <td class="${r.result > 0 ? "positive" : "negative"}">${formatCurrency(r.result)}</td>`;
    tbody.appendChild(row);
  });
}

function updateReportData() {
  const period = document.getElementById("reportPeriod")?.value || "";
  showNotification(`Actualizando reporte ${period}`, "info");
  setTimeout(() => {
    loadReports();
    showNotification("Reporte actualizado", "success");
  }, 800);
}

function exportReport(format, ev) {
  const e = ev || window.event || null;
  const btn = e?.currentTarget || e?.target || null;

  if (btn) btn.classList.add("loading");
  showNotification(`Exportando reporte en formato ${format.toUpperCase()}...`, "info");

  setTimeout(() => {
    if (btn) btn.classList.remove("loading");
    showNotification(`Reporte exportado exitosamente en ${format.toUpperCase()}`, "success");
    // Simulación de descarga
    const link = document.createElement("a");
    link.href = "#";
    link.download = `reporte_tributario.${format}`;
    link.click();
  }, 1200);
}

// ==== Validación SII (simulada) ====
function validateDocument() {
  const folio   = document.getElementById("folioInput")?.value || "";
  const rut     = document.getElementById("rutInput")?.value || "";
  const docType = document.getElementById("docTypeValidation")?.value || "";

  if (!folio || !rut || !docType) {
    showNotification("Por favor complete todos los campos", "error");
    return;
  }

  const btn = document.getElementById("validateBtn");
  const resultDiv = document.getElementById("validationResult");
  if (!btn || !resultDiv) return;

  btn.classList.add("loading");
  btn.disabled = true;
  resultDiv.innerHTML = '<div class="loading-spinner">Validando documento...</div>';

  setTimeout(() => {
    btn.classList.remove("loading");
    btn.disabled = false;

    const isValid = Math.random() > 0.3;
    if (isValid) {
      resultDiv.innerHTML = `
        <div class="validation-success">
          <i class="fas fa-check-circle"></i>
          <h4>Documento Válido</h4>
          <div class="validation-details">
            <p><strong>Folio:</strong> ${folio}</p>
            <p><strong>RUT Emisor:</strong> ${rut}</p>
            <p><strong>Estado:</strong> Documento válido en SII</p>
            <p><strong>Fecha Emisión:</strong> 15/01/2024</p>
            <p><strong>Monto:</strong> $150.000</p>
          </div>
        </div>`;
    } else {
      resultDiv.innerHTML = `
        <div class="validation-error">
          <i class="fas fa-times-circle"></i>
          <h4>Documento No Válido</h4>
          <div class="validation-details">
            <p><strong>Folio:</strong> ${folio}</p>
            <p><strong>RUT Emisor:</strong> ${rut}</p>
            <p><strong>Error:</strong> Documento no encontrado en SII</p>
            <p><strong>Código Error:</strong> DOC_NOT_FOUND</p>
          </div>
        </div>`;
    }
    showNotification(isValid ? "Documento validado exitosamente" : "Error en validación", isValid ? "success" : "error");
  }, 1500);
}

// ==== Utilidades ====
function formatCurrency(amount) {
  return new Intl.NumberFormat("es-CL", { style: "currency", currency: "CLP" }).format(amount);
}
function formatDate(dateString) {
  const d = new Date(dateString);
  return isNaN(d) ? dateString : d.toLocaleDateString("es-CL");
}
function capitalizeFirst(str) {
  return str ? str.charAt(0).toUpperCase() + str.slice(1) : "";
}

// ==== Notificaciones ====
function showNotification(message, type = "info") {
  const notification = document.createElement("div");
  notification.className = `notification notification-${type}`;
  notification.innerHTML = `
    <i class="fas fa-${getNotificationIcon(type)}"></i>
    <span>${message}</span>
    <button aria-label="Cerrar notificación"><i class="fas fa-times"></i></button>
  `;
  notification.querySelector("button").addEventListener("click", () => notification.remove());
  document.body.appendChild(notification);
  setTimeout(() => notification.remove(), 5000);
}
function getNotificationIcon(type) {
  switch (type) {
    case "success": return "check-circle";
    case "error":   return "exclamation-circle";
    case "warning": return "exclamation-triangle";
    default:        return "info-circle";
  }
}

// Inyecta estilos mínimos para notificaciones/validación si no están en CSS
const notificationStyles = `
.notification{position:fixed;top:100px;right:20px;background:#fff;padding:1rem 1.5rem;border-radius:8px;
  box-shadow:0 4px 12px rgba(0,0,0,.15);display:flex;align-items:center;gap:1rem;z-index:1001;min-width:300px;animation:slideIn .3s ease}
.notification-success{border-left:4px solid #10b981}
.notification-error{border-left:4px solid #ef4444}
.notification-warning{border-left:4px solid #f59e0b}
.notification-info{border-left:4px solid #3b82f6}
.notification i:first-child{font-size:1.25rem}
.notification-success i:first-child{color:#10b981}
.notification-error i:first-child{color:#ef4444}
.notification-warning i:first-child{color:#f59e0b}
.notification-info i:first-child{color:#3b82f6}
.notification button{background:none;border:none;cursor:pointer;color:#6b7280;margin-left:auto}
.notification button:hover{color:#374151}
.validation-success,.validation-error{text-align:center;padding:2rem}
.validation-success i,.validation-error i{font-size:3rem;margin-bottom:1rem}
.validation-success i{color:#10b981}.validation-error i{color:#ef4444}
.validation-success h4{color:#10b981;margin-bottom:1rem}
.validation-error h4{color:#ef4444;margin-bottom:1rem}
.validation-details{text-align:left;background:#f8fafc;padding:1rem;border-radius:8px;margin-top:1rem}
.validation-details p{margin-bottom:.5rem;font-size:.9rem}
@keyframes slideIn{from{transform:translateX(100%);opacity:0}to{transform:translateX(0);opacity:1}}
`;
const styleTag = document.createElement("style");
styleTag.textContent = notificationStyles;
document.head.appendChild(styleTag);

// ==== Mini charts en cards (home) ====
function renderMiniCharts() {
  const docsCanvas = document.getElementById("docsChart");
  if (docsCanvas) {
    const ctx = docsCanvas.getContext("2d");
    renderLineChart(ctx, [180,195,210,225,240,247], "#10b981", docsCanvas.width, docsCanvas.height);
  }
  const expenseCanvas = document.getElementById("expenseTrend");
  if (expenseCanvas) {
    const ctx = expenseCanvas.getContext("2d");
    renderLineChart(ctx, [16000000,15800000,15600000,15400000,15300000,15234890], "#ef4444", expenseCanvas.width, expenseCanvas.height);
  }
}
function renderLineChart(ctx, data, color, width = 100, height = 40) {
  const max = Math.max(...data), min = Math.min(...data), range = Math.max(max - min, 1);
  ctx.clearRect(0, 0, width, height);
  ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.lineCap = "round"; ctx.lineJoin = "round";
  ctx.beginPath();
  data.forEach((v, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((v - min) / range) * height;
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.stroke();
  // relleno degradado
  ctx.lineTo(width, height); ctx.lineTo(0, height); ctx.closePath();
  const g = ctx.createLinearGradient(0, 0, 0, height);
  g.addColorStop(0, color + "40"); g.addColorStop(1, color + "00");
  ctx.fillStyle = g; ctx.fill();
}

// ==== Actividad: filtros (home) ====
function setupActivityFilters() {
  const filterBtns = document.querySelectorAll(".filter-btn");
  const items = document.querySelectorAll(".timeline-item");
  if (!filterBtns.length || !items.length) return;

  filterBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      filterBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const filter = btn.getAttribute("data-filter");
      items.forEach((item) => {
        if (filter === "all") { item.style.display = "flex"; return; }
        const type = item.getAttribute("data-type");
        // 'uploads' -> 'upload', 'validations' -> 'validation', 'exports' -> 'export'
        const singular = filter.replace(/s$/, "");
        item.style.display = (type === singular) ? "flex" : "none";
      });
    });
  });
}

// ==== Polyfill roundRect (por si faltara) ====
if (typeof CanvasRenderingContext2D !== "undefined" && !CanvasRenderingContext2D.prototype.roundRect) {
  CanvasRenderingContext2D.prototype.roundRect = function (x, y, w, h, r) {
    this.beginPath();
    this.moveTo(x + r, y);
    this.lineTo(x + w - r, y);
    this.quadraticCurveTo(x + w, y, x + w, y + r);
    this.lineTo(x + w, y + h - r);
    this.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    this.lineTo(x + r, y + h);
    this.quadraticCurveTo(x, y + h, x, y + h - r);
    this.lineTo(x, y + r);
    this.quadraticCurveTo(x, y, x + r, y);
    this.closePath();
  };
}
