const listUrl = "/app/documentos/api/list/";
const uploadUrl = "/app/documentos/api/upload/";

const tbody = document.getElementById("documentsTableBody");
const btnFilter = document.getElementById("btnFilter");
const dateFrom = document.getElementById("dateFrom");
const dateTo = document.getElementById("dateTo");
const docType = document.getElementById("docType");
const docStatus = document.getElementById("docStatus");

// Upload
const uploadArea = document.getElementById("uploadArea");
const fileInput = document.getElementById("fileInput");
const btnSelect = document.getElementById("btnSelect");
const uploadForm = document.getElementById("uploadForm");

// CSRF
function getCookie(name) {
  const v = `; ${document.cookie}`.split(`; ${name}=`);
  if (v.length === 2) return v.pop().split(";").shift();
}
const csrftoken = getCookie("csrftoken");

btnSelect?.addEventListener("click", () => fileInput.click());
uploadArea?.addEventListener("click", () => fileInput.click());
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
  if (e.dataTransfer?.files?.length) {
    doUpload(e.dataTransfer.files);
  }
});
fileInput?.addEventListener("change", () => {
  if (fileInput.files?.length) doUpload(fileInput.files);
});

async function doUpload(files) {
  const fd = new FormData();
  // backend acepta "files[]" o "files"
  for (const f of files) fd.append("files[]", f);

  const res = await fetch(uploadUrl, {
    method: "POST",
    headers: { "X-CSRFToken": csrftoken },
    body: fd,
  });
  if (!res.ok) {
    const text = await res.text();
    alert("Error al subir: " + text);
    return;
  }
  const data = await res.json();
  let msg = `Subidos: ${data.created}`;
  if (data.skipped) msg += ` | Duplicados: ${data.skipped}`;
  if (data.errors?.length) msg += ` | Errores: ${data.errors.join(", ")}`;
  alert(msg);
  fileInput.value = "";
  loadDocuments(); // refrescar tabla
}

btnFilter?.addEventListener("click", () => loadDocuments());

async function loadDocuments() {
  const params = new URLSearchParams();
  if (dateFrom.value) params.set("dateFrom", dateFrom.value);
  if (dateTo.value) params.set("dateTo", dateTo.value);
  if (docType.value) params.set("docType", docType.value);
  if (docStatus.value) params.set("docStatus", docStatus.value);

  const res = await fetch(listUrl + "?" + params.toString(), {
    headers: { Accept: "application/json" },
  });
  if (!res.ok) {
    tbody.innerHTML = `<tr><td colspan="7">Error al cargar documentos</td></tr>`;
    return;
  }
  const data = await res.json();
  renderRows(data.results || []);
}

function renderRows(rows) {
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="7">No hay documentos</td></tr>`;
    return;
  }
  tbody.innerHTML = rows
    .map(
      (r) => `
    <tr>
      <td>${r.fecha}</td>
      <td>${r.tipo || "—"}</td>
      <td>${r.folio || "—"}</td>
      <td>${r.rut_emisor || "—"}</td>
      <td>${
        r.monto == null
          ? "—"
          : new Intl.NumberFormat("es-CL", {
              style: "currency",
              currency: "CLP",
            }).format(r.monto)
      }</td>
      <td>${r.estado || "—"}</td>
      <td>
        ${
          r.archivo_url
            ? `<a href="${r.archivo_url}" target="_blank" rel="noopener">Ver</a>`
            : ""
        }
      </td>
    </tr>
  `
    )
    .join("");
}

// carga inicial
document.addEventListener("DOMContentLoaded", loadDocuments);
