(function () {
  let el = null, 
  timer = null;

  function ensureToast() {
    if (!el) {
      el = document.createElement("div");
      el.className = "toast";
      el.setAttribute("role", "status");
      document.body.appendChild(el);
    }
    return el;
  }

  window.showNotification = function (message, type = "success") {
    const t = ensureToast();
    t.className = "toast show " + (type === "error" ? "error" : "success");
    t.textContent = message;
    clearTimeout(timer);
    timer = setTimeout(() => {
      t.classList.remove("show");
    }, 2200);
  };

  // === Tabs ===
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      const target = document.getElementById(btn.dataset.tab);
      if (target) target.classList.add('active');
    });
  });

  // === Feedback inmediato al guardar ajustes ===
  const form = document.getElementById('generalSettingsForm');
  if (form) {
    form.addEventListener('submit', function () {
      showNotification("Guardando configuración…", "success");
    });
  }
})();