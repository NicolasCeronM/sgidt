(function () {
  "use strict";

  function $(sel, ctx) {
    return (ctx || document).querySelector(sel);
  }
  function $all(sel, ctx) {
    return Array.from((ctx || document).querySelectorAll(sel));
  }

  document.addEventListener("DOMContentLoaded", function () {
    var input = $("#dbxSearch");
    var table = $("#dbxTableBody");
    var rows = table ? $all("tr", table) : [];
    var refreshBtn = $("#dbxRefreshBtn");

    // --- Filtro por nombre (client-side) ---
    if (input && table) {
      input.addEventListener("input", function () {
        var q = input.value.trim().toLowerCase();

        rows.forEach(function (tr) {
          var tdName = tr.querySelector('td[data-col="name"]');
          var name = tdName ? tdName.textContent.trim().toLowerCase() : "";
          tr.style.display = name.includes(q) ? "" : "none";
        });
      });

      // Enter no hace submit ni nada raro
      input.addEventListener("keydown", function (e) {
        if (e.key === "Enter") e.preventDefault();
      });
    }

    // --- Refrescar listado ---
    if (refreshBtn) {
      refreshBtn.addEventListener("click", function () {
        // Mantiene el scroll del usuario
        var y = window.scrollY || 0;
        window.location.reload();
        window.scrollTo(0, y);
      });
    }

    // --- Accesibilidad: foco visible al tabular en enlaces "Abrir" ---
    $all(".link-open").forEach(function (a) {
      a.addEventListener("focus", function () {
        a.style.outline = "2px solid rgba(30,64,175,.6)";
        a.style.outlineOffset = "2px";
      });
      a.addEventListener("blur", function () {
        a.style.outline = "none";
      });
    });
  });
})();
