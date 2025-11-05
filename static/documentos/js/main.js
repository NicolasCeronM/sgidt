// static/panel/js/documentos/main.js
import { wireUpload } from "./upload.js";
import { wireFilters } from "./list.js";

document.addEventListener("DOMContentLoaded", () => {
  wireUpload();
  wireFilters();

  // --- NUEVA LÓGICA ---
  // Para el botón de "Subir Documento" que muestra/oculta el panel
  const btnToggleUpload = document.getElementById("btnToggleUpload");
  const uploadContainer = document.getElementById("uploadContainer");

  btnToggleUpload?.addEventListener("click", () => {
    const isHidden = uploadContainer.hidden;
    uploadContainer.hidden = !isHidden;
    btnToggleUpload.setAttribute("aria-expanded", isHidden);
  });
  // --- FIN NUEVA LÓGICA ---

  document.getElementById("empty-upload")?.addEventListener("click", (e) => {
    e.preventDefault();
    // Si el panel de subida está oculto, lo mostramos
    if (uploadContainer.hidden) {
        uploadContainer.hidden = false;
        btnToggleUpload.setAttribute("aria-expanded", true);
    }
    // Hacemos scroll hacia el panel de subida
    uploadContainer.scrollIntoView({ behavior: "smooth", block: "start" });
  });
});