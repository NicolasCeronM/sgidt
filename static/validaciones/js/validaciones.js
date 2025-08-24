function validateDocument(e) {
  e.preventDefault();
  const result = document.getElementById("validationResult");
  const docType = document.getElementById("docType").value || "—";
  const number = document.getElementById("docNumber").value || "—";
  const date = document.getElementById("emissionDate").value || "—";
  const amount = document.getElementById("totalAmount").value || "—";

  // Mock de validación
  const ok = number && amount ? Number(amount) % 2 === 0 : false;

  result.innerHTML = `
    <div class="val-box">
      <div class="val-row"><span class="val-label">Estado</span>
        <span class="val-value">
          <span class="badge ${ok ? "ok" : "err"}">${
    ok ? "VÁLIDO" : "INVÁLIDO"
  }</span>
        </span>
      </div>
      <div class="val-row"><span class="val-label">Tipo</span><span class="val-value">${docType}</span></div>
      <div class="val-row"><span class="val-label">N° Documento</span><span class="val-value">${number}</span></div>
      <div class="val-row"><span class="val-label">Fecha</span><span class="val-value">${date}</span></div>
      <div class="val-row"><span class="val-label">Monto</span><span class="val-value">$${new Intl.NumberFormat(
        "es-CL"
      ).format(amount || 0)}</span></div>
    </div>
  `;
}
