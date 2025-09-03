// static/panel/js/documentos/main.js
import { wireUpload } from "./upload.js";
import { wireFilters } from "./list.js";

document.addEventListener("DOMContentLoaded", ()=>{
  wireUpload();
  wireFilters();
  document.getElementById('empty-upload')?.addEventListener('click', () => {
    document.getElementById('fileInput')?.click();
  });
});
