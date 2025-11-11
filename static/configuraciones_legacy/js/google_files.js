(function () {
  // Búsqueda rápida por nombre
  var input = document.getElementById("gdSearch");
  var tbody = document.getElementById("gdTableBody");

  if (input && tbody) {
    var rows = Array.prototype.slice.call(tbody.querySelectorAll("tr"));

    input.addEventListener("input", function () {
      var q = (this.value || "").toLowerCase().trim();
      rows.forEach(function (row) {
        var cell = row.querySelector('[data-col="name"]');
        var name = (
          cell && cell.textContent ? cell.textContent : ""
        ).toLowerCase();
        row.style.display = name.indexOf(q) > -1 ? "" : "none";
      });
    });
  }

  // Refrescar
  var refreshBtn = document.getElementById("gdRefreshBtn");
  if (refreshBtn) {
    refreshBtn.addEventListener("click", function () {
      window.location.reload();
    });
  }
})();
