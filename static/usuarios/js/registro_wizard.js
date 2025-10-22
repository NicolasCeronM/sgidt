// === PROGRESO DEL REGISTRO ===
(function () {
  const wizard = document.getElementById("wizard");
  if (!wizard) return;
  const step = Number(wizard.dataset.step || 1);
  const total = Number(wizard.dataset.total || 1);
  const percent = Math.round((step / total) * 100);
  const bar = document.getElementById("progress-bar");
  if (bar) bar.style.width = percent + "%";
})();

// === OCULTAR CAMPOS SI PN_HONORARIOS ===
(function () {
  if (typeof tipoActual === "undefined" || tipoActual !== "PN_HONORARIOS") return;
  [
    'select[name="sistema_facturacion"]',
    'input[name="certificado_usa"]',
    'input[name="tipos_dte_autorizados"]',
  ].forEach((sel) => {
    const el = document.querySelector(sel);
    el?.closest("p")?.setAttribute("style", "display:none");
  });
})();
