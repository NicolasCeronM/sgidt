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
    // Cierra cualquier otro modal abierto
    document.querySelectorAll(".chatbot-modal.active").forEach((m) => {
      m.classList.remove("active");
      m.setAttribute("aria-hidden", "true");
    });

    // Abre el nuevo
    modal.classList.add("active");
    modal.setAttribute("aria-hidden", "false");
    const input = modal.querySelector("input, textarea");
    if (input) setTimeout(() => input.focus(), 50);
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

  // ✅ NUEVA LÓGICA DE CIERRE
  document.querySelectorAll('[data-close="true"]').forEach((btn) => {
    btn.addEventListener("click", (e) => {
      const modal = e.target.closest(".chatbot-modal");
      if (modal) {
        modal.classList.remove("active");
        modal.setAttribute("aria-hidden", "true");
      }
    });
  });

  // Cerrar con tecla Escape
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      document.querySelectorAll(".chatbot-modal.active").forEach((m) => {
        m.classList.remove("active");
        m.setAttribute("aria-hidden", "true");
      });
    }
  });
})();


// --- LÓGICA ESPECÍFICA PARA LA CALCULADORA DE IVA ---
// --- LÓGICA ESPECÍFICA PARA LA CALCULADORA DE IVA (CON NUEVO DISEÑO) ---
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
      resultDiv.innerHTML = '<p class="placeholder" style="color: #e53e3e;">Expresión inválida</p>';
      return;
    }
    
    // Si solo se calcula la expresión
    if (mode === "none" || !rate) {
      resultDiv.innerHTML = `<p class="total-line"><span>Total:</span> <span class="result-value">$ ${fmt(
        baseAmount
      )}</span></p>`;
      return;
    }

    const ivaData = calcIVA(baseAmount, rate, mode);
    if (!ivaData) {
      resultDiv.innerHTML = '<p class="placeholder" style="color: #e53e3e;">Tasa de IVA inválida</p>';
      return;
    }
    
    // Formateo del resultado final para el nuevo diseño
    resultDiv.innerHTML = `
      <p><span>Monto Base:</span> <span class="result-value">$ ${fmt(ivaData.base)}</span></p>
      <p><span>IVA (${parseFloat(rate).toFixed(2).replace(".", ",")} %):</span> <span class="result-value">$ ${fmt(ivaData.iva)}</span></p>
      <p class="total-line"><span>Total:</span> <span class="result-value">$ ${fmt(ivaData.total)}</span></p>
    `;
  });
});
