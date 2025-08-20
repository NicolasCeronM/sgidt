// Sidebar móvil (hamburguesa) – SGIDT
(function () {
  const mq = window.matchMedia("(max-width: 900px)");
  const body = document.body;

  const sidebar = document.getElementById("sidebar");
  const openBtn = document.getElementById("sidebarHamburger");
  const backdrop = document.getElementById("sidebarBackdrop");
  // closeBtn ya no es necesario, pero dejar nulo no rompe nada
  const closeBtn = document.getElementById("sidebarClose");

  if (!sidebar) return;

  const links = sidebar.querySelectorAll(".sidebar-link");

  function openSidebar() {
    if (!mq.matches) return; // solo móvil
    body.classList.add("sidebar-open", "sidebar-noscroll");
    sidebar.setAttribute("aria-hidden", "false");
    openBtn && openBtn.setAttribute("aria-expanded", "true");
    backdrop && backdrop.removeAttribute("hidden");
  }

  function closeSidebar() {
    body.classList.remove("sidebar-open", "sidebar-noscroll");
    sidebar.setAttribute("aria-hidden", "true");
    openBtn && openBtn.setAttribute("aria-expanded", "false");
    backdrop && backdrop.setAttribute("hidden", "");
  }

  // Abrir
  openBtn &&
    openBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      openSidebar();
    });

  // Cerrar con backdrop
  backdrop && backdrop.addEventListener("click", closeSidebar);

  // Cerrar con Escape
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeSidebar();
  });

  // Cerrar al navegar dentro del menú (en móvil)
  links.forEach((a) => {
    a.addEventListener("click", () => {
      if (mq.matches) closeSidebar();
    });
  });

  // Cerrar si se hace click en cualquier lugar fuera del sidebar y del botón
  document.addEventListener("click", (e) => {
    if (!body.classList.contains("sidebar-open")) return;
    const clickDentroSidebar = sidebar.contains(e.target);
    const clickEnHamburguesa = openBtn && openBtn.contains(e.target);
    if (!clickDentroSidebar && !clickEnHamburguesa) {
      closeSidebar();
    }
  });

  // Si pasa a desktop, cerrar
  window.addEventListener("resize", () => {
    if (!mq.matches) closeSidebar();
  });
})();
