// --- LÓGICA PARA MARCAR EL LINK ACTIVO EN EL MENÚ ---
(function () {
  const here = location.pathname.replace(/\/+$/, "");
  document.querySelectorAll(".sidebar-link, .nav-link").forEach((a) => {
    const href = a.getAttribute("href")?.replace(/\/+$/, "");
    if (href && (here === href || (href === "" && here === "/"))) {
      a.classList.add("is-active");
      a.setAttribute("aria-current", "page");
    }
  });
})();

// --- LÓGICA UNIFICADA PARA EL MENÚ FLOTANTE Y MODALES ---
(function () {
  const fabContainer = document.querySelector(".fab-container");
  const fabMain = document.getElementById("fab-main");
  const chatTrigger = document.getElementById("fab-chat-trigger");
  const calcTrigger = document.getElementById("fab-calc-trigger");
  const chatbotModal = document.getElementById("chatbotModal");
  const civaModal = document.getElementById("civaModal");

  if (!fabMain || !chatbotModal || !civaModal) return;

  const openModal = (modal) => {
    modal.classList.add("active");
    modal.setAttribute("aria-hidden", "false");
    const input = modal.querySelector("input, textarea");
    if (input) setTimeout(() => input.focus(), 50);
  };

  const closeModal = () => {
    const activeModal = document.querySelector(".chatbot-modal.active");
    if (activeModal) {
      activeModal.classList.remove("active");
      activeModal.setAttribute("aria-hidden", "true");
    }
  };

  fabMain.addEventListener("click", () => {
    fabContainer.classList.toggle("active");
    fabMain.classList.toggle("active");
  });

  const openWidget = (modal) => {
    openModal(modal);
    fabContainer.classList.remove("active");
    fabMain.classList.remove("active");
  };

  chatTrigger.addEventListener("click", () => openWidget(chatbotModal));
  calcTrigger.addEventListener("click", () => openWidget(civaModal));

  document
    .querySelectorAll(".chatbot-close, .chatbot-backdrop")
    .forEach((el) => {
      el.addEventListener("click", closeModal);
    });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && document.querySelector(".chatbot-modal.active")) {
      closeModal();
    }
  });
})();

// --- LÓGICA ESPECÍFICA PARA LA CALCULADORA DE IVA ---
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("civaForm");
  const resultDiv = document.getElementById("civaResult");

  function safeEval(expr) {
    expr = expr.replace(/(\d+(\.\d+)?)\s*%/g, "($1/100)");
    if (/[^-()\d/*+. \t]/.test(expr)) return null;
    try {
      return new Function("return " + expr)();
    } catch {
      return null;
    }
  }

  function calcIVA(amount, rate, mode) {
    const rateNum = parseFloat(rate);
    if (isNaN(rateNum) || rateNum < 0) return null;
    if (mode === "neto") {
      const iva = (amount * rateNum) / 100;
      return { base: amount, iva, total: amount + iva };
    } else if (mode === "total") {
      const base = amount / (1 + rateNum / 100);
      const iva = amount - base;
      return { base, iva, total: amount };
    }
    return null;
  }

  const fmt = (num) => {
    if (typeof num !== "number" || isNaN(num)) return "0";
    return Math.round(num)
      .toString()
      .replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  };

  form?.addEventListener("submit", (e) => {
    e.preventDefault();
    const expr = form.expression.value.trim();
    const rate = form.rate.value.trim();
    const mode = form.mode.value;
    const baseAmount = safeEval(expr);

    if (baseAmount === null) {
      resultDiv.innerHTML = '<p style="color:red;">Expresión inválida</p>';
      return;
    }
    if (mode === "none" || !rate) {
      resultDiv.innerHTML = `<p><strong>Resultado:</strong></p><p>Monto final: ${fmt(
        baseAmount
      )}</p>`;
      return;
    }
    const ivaData = calcIVA(baseAmount, rate, mode);
    if (!ivaData) {
      resultDiv.innerHTML = '<p style="color:red;">Tasa de IVA inválida</p>';
      return;
    }
    resultDiv.innerHTML = `
          <p><strong>Resultados:</strong></p>
          <p>Base imponible: ${fmt(ivaData.base)}</p>
          <p>IVA (${parseFloat(rate).toFixed(2).replace(".", ",")}%): ${fmt(
      ivaData.iva
    )}</p>
          <p><strong>Total: ${fmt(ivaData.total)}</strong></p>
        `;
  });
});
