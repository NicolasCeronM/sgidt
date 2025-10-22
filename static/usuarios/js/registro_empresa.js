  console.log("✅ registro_empresa.js cargado");
 
$(document).ready(function() {

  console.log("✅ DOM listo, buscando #id_empresa_rut");
 
  const input = $('#id_empresa_rut');

  if (input.length === 0) {

    console.warn("⚠️ No se encontró el input con id #id_empresa_rut");

  } else {

    console.log("👍 Input encontrado, asignando evento blur");

  }
 
  input.on('blur', function() {

    console.log("🎯 Evento blur detectado:", $(this).val());

  });

});
 
  
  
  
  function setPlaceholder(id, text) {
  const el = document.getElementById(id);
  if (el && !el.placeholder) el.placeholder = text;
}

// Inserta/actualiza mensaje de error SIN alterar la altura del contenedor del input
function showError(input, msg) {
  input.setAttribute("aria-invalid", "true");

  // Contenedor de grupo (no el de icono)
  const group = input.closest(".form-group") || input.parentElement;

  // Localiza/cimbra un error asociado a este input
  let err = group.querySelector('.field-error[data-for="' + input.id + '"]');
  if (!err) {
    err = document.createElement("div");
    err.className = "field-error";
    err.setAttribute("data-for", input.id); // para no mezclar errores entre campos
    // Colócalo AL FINAL del .form-group, así no afecta el alto del input
    group.appendChild(err);
  }
  err.textContent = msg;
}

// Limpia el error correspondiente
function clearError(input) {
  input.removeAttribute("aria-invalid");
  const group = input.closest(".form-group") || input.parentElement;
  const err = group.querySelector('.field-error[data-for="' + input.id + '"]');
  if (err) err.remove();
}

// -------------- Validadores de datos --------------
function normalizarRut(v) {
  return (v || "")
    .replace(/\./g, "")
    .replace(/-/g, "")
    .replace(/\s+/g, "")
    .toUpperCase();
}

function validarRutChile(v) {
  v = normalizarRut(v);
  if (!/^\d{7,8}[0-9K]$/.test(v)) return false;
  const cuerpo = v.slice(0, -1),
    dv = v.slice(-1);
  let suma = 0,
    mult = 2;
  for (let i = cuerpo.length - 1; i >= 0; i--) {
    suma += parseInt(cuerpo[i], 10) * mult;
    mult = mult === 7 ? 2 : mult + 1;
  }
  const res = 11 - (suma % 11);
  const dvCalc = res === 11 ? "0" : res === 10 ? "K" : String(res);
  return dvCalc === dv;
}

function validarEmail(v) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);
}

function validarTelefonoCL(v) {
  v = (v || "").replace(/\s+/g, "").trim();
  // +56 9 ######## o líneas fijas chilenas
  return /^(\+?56)?0?9\d{8}$/.test(v) || /^(\+?56)?\d{9}$/.test(v);
}

// Reglas mínimas: 8+, letras y números
function passRequisitos(p) {
  const largo = p.length >= 8;
  const letras = /[A-Za-z]/.test(p);
  const numeros = /\d/.test(p);
  return { ok: largo && letras && numeros, largo, letras, numeros };
}

// -------------- Medidor de fuerza de contraseña --------------
function scorePassword(p, ctxText = "") {
  let score = 0;
  if (!p) return 0;

  const length = p.length;
  const hasLower = /[a-z]/.test(p);
  const hasUpper = /[A-Z]/.test(p);
  const hasDigit = /\d/.test(p);
  const hasSym = /[^A-Za-z0-9]/.test(p);

  // Base por longitud
  if (length >= 8) score += 1;
  if (length >= 10) score += 1;
  if (length >= 14) score += 1;

  // Variedad de caracteres
  const kinds = [hasLower, hasUpper, hasDigit, hasSym].filter(Boolean).length;
  if (kinds >= 2) score += 1;
  if (kinds >= 3) score += 1;

  // Penaliza si contiene partes del contexto (email/nombre/razón)
  if (ctxText) {
    const tokens = ctxText
      .toLowerCase()
      .split(/[\s@._-]+/)
      .filter((t) => t.length >= 3);
    for (const t of tokens) {
      if (t && p.toLowerCase().includes(t)) {
        score -= 1;
        break;
      }
    }
  }

  // Contraseñas comunes
  const comunes = [
    "password",
    "123456",
    "qwerty",
    "admin",
    "welcome",
    "abc123",
    "111111",
    "iloveyou",
    "12345678",
    "000000",
  ];
  if (comunes.some((c) => p.toLowerCase().includes(c)))
    score = Math.max(0, score - 2);

  // Normaliza 0..4
  return Math.max(0, Math.min(4, score));
}

// -------------- Formateo de RUT en vivo --------------
function formatearRut(v) {
  v = normalizarRut(v);
  if (!v) return "";
  const dv = v.slice(-1);
  let cuerpo = v.slice(0, -1);
  let f = "";
  while (cuerpo.length > 3) {
    f = "." + cuerpo.slice(-3) + f;
    cuerpo = cuerpo.slice(0, -3);
  }
  f = cuerpo + f;
  return f ? `${f}-${dv}` : v;
}

function bindRutFormato(el) {
  if (!el) return;
  el.addEventListener("input", () => {
    const posEnd = el.selectionEnd; // caret simple al final
    el.value = formatearRut(el.value);
    el.setSelectionRange(el.value.length, el.value.length);
  });
  el.addEventListener("blur", () => {
    el.value = formatearRut(el.value);
  });
}

// -------------- Main --------------
(function () {
  const form = document.getElementById("registroEmpresaForm");
  if (!form) return;

  // Campos (IDs por defecto de Django)
  const f = {
    empresa_rut: document.getElementById("id_empresa_rut"),
    razon_social: document.getElementById("id_razon_social"),
    tipo_societario: document.getElementById("id_tipo_societario"),
    regimen_tributario: document.getElementById("id_regimen_tributario"),
    giro: document.getElementById("id_giro"),
    codigo_actividad: document.getElementById("id_codigo_actividad"),
    email_empresa: document.getElementById("id_email_empresa"),
    telefono: document.getElementById("id_telefono"),
    direccion: document.getElementById("id_direccion"),
    comuna: document.getElementById("id_comuna"),
    region: document.getElementById("id_region"),
    first_name: document.getElementById("id_first_name"),
    last_name: document.getElementById("id_last_name"),
    user_email: document.getElementById("id_user_email"),
    user_rut: document.getElementById("id_user_rut"),
    password1: document.getElementById("id_password1"),
    password2: document.getElementById("id_password2"),
    terminos: document.getElementById("id_aceptar_terminos"),
  };

  // Placeholders de ayuda (por si no vienen desde el backend)
  setPlaceholder("id_empresa_rut", "12.345.678-9");
  setPlaceholder("id_razon_social", "Mi Empresa SpA");
  setPlaceholder("id_giro", "Comercio al por menor de ferretería");
  setPlaceholder("id_codigo_actividad", "123456");
  setPlaceholder("id_email_empresa", "contacto@empresa.cl");
  setPlaceholder("id_telefono", "+56 9 1234 5678");
  setPlaceholder("id_direccion", "Calle 123, Oficina 45");
  setPlaceholder("id_comuna", "Maipú");
  setPlaceholder("id_region", "Región Metropolitana");
  setPlaceholder("id_first_name", "Nombre");
  setPlaceholder("id_last_name", "Apellido");
  setPlaceholder("id_user_email", "correo@dominio.cl");
  setPlaceholder("id_user_rut", "12.345.678-9");
  setPlaceholder("id_password1", "••••••••");
  setPlaceholder("id_password2", "••••••••");

  // Toggle mostrar/ocultar contraseña (botones con .toggle-password)
  document.querySelectorAll(".toggle-password").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-target");
      const input = document.getElementById(id);
      if (!input) return;
      const show = input.type === "password";
      input.type = show ? "text" : "password";
      btn.classList.toggle("is-on", show); // cambia icono via CSS
    });
  });

  // Medidor de fuerza de contraseña (requiere contenedor en HTML)
  const meter = document.getElementById("pwd-meter");
  const fill = meter ? meter.querySelector(".pwd-meter-fill") : null;
  const text = meter ? meter.querySelector(".pwd-meter-text") : null;

  function updateMeter() {
    if (!f.password1 || !meter || !fill || !text) return;
    const ctx = [
      (f.user_email && f.user_email.value) || "",
      (f.first_name && f.first_name.value) || "",
      (f.last_name && f.last_name.value) || "",
      (f.razon_social && f.razon_social.value) || "",
    ].join(" ");
    const s = scorePassword(f.password1.value, ctx);
    const widths = ["0%", "25%", "50%", "75%", "100%"];
    const colors = ["#ef4444", "#f59e0b", "#f59e0b", "#10b981", "#059669"];
    const labels = ["Muy débil", "Débil", "Aceptable", "Buena", "Fuerte"];
    fill.style.width = widths[s];
    fill.style.backgroundColor = colors[s];
    text.textContent = "Fuerza: " + labels[s];
    meter.setAttribute("aria-hidden", f.password1.value ? "false" : "true");
  }
  if (f.password1) {
    f.password1.addEventListener("input", updateMeter);
    f.password1.addEventListener("blur", updateMeter);
    updateMeter();
  }

  // Formateo RUT en vivo
  bindRutFormato(f.empresa_rut);
  bindRutFormato(f.user_rut);

  // Validadores por campo (on blur)
  const validators = {
    empresa_rut: (el) => {
      const v = el.value.trim();
      if (!v) {
        showError(el, "Ingresa el RUT de la empresa.");
        return false;
      }
      if (!validarRutChile(v)) {
        showError(el, "RUT inválido. Usa formato 12.345.678-9");
        return false;
      }
      clearError(el);
      return true;
    },
    razon_social: (el) => {
      if (!el.value.trim()) {
        showError(el, "Ingresa la razón social.");
        return false;
      }
      clearError(el);
      return true;
    },
    user_email: (el) => {
      const v = el.value.trim();
      if (!v || !validarEmail(v)) {
        showError(el, "Correo inválido. Ej: correo@dominio.cl");
        return false;
      }
      clearError(el);
      return true;
    },
    user_rut: (el) => {
      const v = el.value.trim();
      if (!v) {
        clearError(el);
        return true;
      }
      if (!validarRutChile(v)) {
        showError(el, "RUT del representante inválido.");
        return false;
      }
      clearError(el);
      return true;
    },
    codigo_actividad: (el) => {
      const v = el.value.trim();
      if (!v) {
        clearError(el);
        return true;
      }
      if (!/^\d{6}$/.test(v)) {
        showError(el, "Debe tener 6 dígitos.");
        return false;
      }
      clearError(el);
      return true;
    },
    telefono: (el) => {
      const v = el.value.trim();
      if (!v) {
        clearError(el);
        return true;
      }
      if (!validarTelefonoCL(v)) {
        showError(el, "Formato inválido. Ej: +56 9 1234 5678");
        return false;
      }
      clearError(el);
      return true;
    },
    password1: (el) => {
      const p = el.value;
      const r = passRequisitos(p);
      if (!r.ok) {
        showError(
          el,
          "La contraseña debe tener al menos 8 caracteres e incluir letras y números."
        );
        return false;
      }
      clearError(el);
      updateMeter();
      return true;
    },
    password2: (el) => {
      if (el.value !== (f.password1 ? f.password1.value : "")) {
        showError(el, "Las contraseñas no coinciden.");
        return false;
      }
      clearError(el);
      return true;
    },
  };

  Object.entries(validators).forEach(([name, fn]) => {
    const el = f[name];
    if (!el) return;
    el.addEventListener("blur", () => fn(el));
    el.addEventListener("input", () => clearError(el));
  });

  // Spinner de envío + validación final
  form.addEventListener("submit", (e) => {
    let ok = true;

    // Valida los campos críticos
    [
      "empresa_rut",
      "razon_social",
      "user_email",
      "user_rut",
      "codigo_actividad",
      "telefono",
      "password1",
      "password2",
    ].forEach((n) => {
      if (f[n] && validators[n]) ok = validators[n](f[n]) && ok;
    });

    // Términos y condiciones
    if (f.terminos && !f.terminos.checked) {
      const wrap =
        f.terminos.closest(".form-checkbox") || f.terminos.parentElement;
      let err = wrap.querySelector(".field-error");
      if (!err) {
        err = document.createElement("div");
        err.className = "field-error";
        wrap.appendChild(err);
      }
      err.textContent = "Debes aceptar los términos y condiciones.";
      ok = false;
    } else {
      const wrap =
        f.terminos.closest(".form-checkbox") || f.terminos.parentElement;
      const err = wrap.querySelector(".field-error");
      if (err) err.remove();
    }

    if (!ok) {
      e.preventDefault();
      // Foco al primer campo inválido
      const primero = form.querySelector('[aria-invalid="true"]');
      if (primero) primero.focus();
      return;
    }

    // Mostrar spinner y deshabilitar botón
    const btn = document.getElementById("submitBtn");
    const txt = document.getElementById("btnText");
    const load = document.getElementById("loading");
    if (btn) {
      btn.disabled = true;
    }
    if (txt) {
      txt.style.display = "none";
    }
    if (load) {
      load.style.display = "inline-block";
    }
  });
})();
