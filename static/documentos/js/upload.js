// static/panel/js/documentos/upload.js
import { uploadUrl, csrftoken } from "./api.js";
import { progressStart, progressDone, showToast } from "./ui.js";

export function wireUpload() {
  const uploadArea = document.getElementById("uploadArea");
  const fileInput = document.getElementById("fileInput");
  const btnSelect = document.getElementById("btnSelect");

  btnSelect?.addEventListener("click", () => fileInput?.click());
  uploadArea?.addEventListener("click", (e) => {
    if (!e.target.closest("button")) fileInput?.click();
  });
  uploadArea?.addEventListener("dragover", (e) => {
    e.preventDefault();
    uploadArea.classList.add("dragging");
  });
  uploadArea?.addEventListener("dragleave", () =>
    uploadArea.classList.remove("dragging")
  );
  uploadArea?.addEventListener("drop", (e) => {
    e.preventDefault();
    uploadArea.classList.remove("dragging");
    if (e.dataTransfer?.files?.length) doUpload(e.dataTransfer.files);
  });
  fileInput?.addEventListener("change", () => {
    if (fileInput.files?.length) doUpload(fileInput.files);
  });

  async function doUpload(files) {
    const fd = new FormData();
    const allowed = [".pdf", ".jpg", ".jpeg", ".png"];
    const max = 10 * 1024 * 1024;
    const added = [];
    for (const f of files) {
      const n = f.name.toLowerCase();
      if (allowed.some((ext) => n.endsWith(ext)) && f.size <= max) {
        fd.append("files[]", f);
        added.push(addQueueItem(f)); // guardamos el <li> para cerrarlo luego
      }
    }
    if (!added.length) return;

    const K = "upload";
    showToast("Subiendo archivos…", "info", { key: K, persist: true });
    progressStart();

    try {
      const res = await fetch(uploadUrl, {
        method: "POST",
        headers: { "X-CSRFToken": csrftoken },
        body: fd,
      });

      // Manejo seguro de respuesta: si es 204 o sin JSON no intentamos parsear
      let data = {};
      const ct = res.headers.get("content-type") || "";
      if (res.ok && ct.includes("application/json")) {
        try {
          data = await res.json();
        } catch {
          data = {};
        }
      } else if (!res.ok) {
        try {
          data = { errors: [await res.text()] };
        } catch {
          data = { errors: ["Error desconocido"] };
        }
      }

      // Mensaje
      const errs = (data.errors || []).map((e) =>
        /UNIQUE constraint.*hash_sha256/i.test(e)
          ? "Archivo duplicado en la empresa"
          : e
      );
      let msg = `Subidos: ${data.created || 0}`;
      if (data.skipped) msg += ` | Duplicados: ${data.skipped}`;
      if (errs.length) msg += ` | Errores: ${errs.join(", ")}`;

      const ok = res.ok;
      showToast(
        msg,
        ok && !errs.length ? "success" : errs.length ? "warning" : "error",
        { key: K, duration: 7000 }
      );

      // Dispara recarga de la tabla
      document.dispatchEvent(new CustomEvent("docs:reload"));
    } catch (err) {
      showToast(`Error de red al subir: ${String(err)}`, "error", {
        key: K,
        duration: 7000,
      });
    } finally {
      progressDone();
      // 🔑 CERRAR SIEMPRE los ítems de la cola con transición
      const q = document.getElementById("queue");
      const items = q ? Array.from(q.querySelectorAll(".q-item")) : [];
      items.forEach((li) => {
        const bar = li.querySelector(".bar");
        if (bar) bar.style.width = "100%";
        li.classList.add("removing");
        setTimeout(() => {
          li.remove();
          if (q && !q.children.length) q.hidden = true;
        }, 250);
      });
    }
  }

  function addQueueItem(file) {
    const q = document.getElementById("queue");
    if (!q) return null;
    q.hidden = false;
    const li = document.createElement("li");
    li.className = "q-item";
    li.innerHTML = `
      <div class="q-file"><i class="fas fa-file"></i><div class="q-meta">
        <strong class="name">${file.name}</strong><small class="size">${(
      file.size /
      1024 /
      1024
    ).toFixed(2)} MB</small></div></div>
      <div class="q-progress"><div class="bar"></div><span class="pct">0%</span></div>`;
    q.appendChild(li);

    // animación “simulada” hasta 92%
    let p = 0;
    const id = setInterval(() => {
      p = Math.min(p + 8, 92);
      li.querySelector(".bar").style.width = p + "%";
      li.querySelector(".pct").textContent = p + "%";
      if (p >= 92) clearInterval(id);
    }, 120);

    return li;
  }
}
