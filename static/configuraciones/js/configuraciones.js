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
})();
