// static/usuarios/registro_persona.js
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("registrationForm");
  if (!form) return;

  const submitBtn = document.getElementById("submitBtn");
  const btnText = document.getElementById("btnText");
  const loading = document.getElementById("loading");
  const successPopup = document.getElementById("successPopup");

  // Campos (selección por data-field, independiente de los IDs reales de Django)
  const fields = {
    first_name: form.querySelector('[data-field="first_name"]'),
    last_name: form.querySelector('[data-field="last_name"]'),
    email: form.querySelector('[data-field="email"]'),
    rut: form.querySelector('[data-field="rut"]'),
    password1: form.querySelector('[data-field="password1"]'),
    password2: form.querySelector('[data-field="password2"]'),
  };

  // Utilidades UI
  const successEl = (name) => form.querySelector(`[data-success="${name}"]`);
  const showSuccess = (name, msg) => {
    const el = successEl(name);
    if (el) {
      el.textContent = msg;
      el.style.display = "block";
    }
  };
  const hideSuccess = (name) => {
    const el = successEl(name);
    if (el) {
      el.style.display = "none";
    }
  };

  const showError = (fieldEl, msg) => {
    // si existe error-message generado por Django, lo respetamos; si no, creamos temporal
    let box = fieldEl
      .closest(".form-group")
      .querySelector(".error-message:not(.django)");
    if (!box) {
      box = document.createElement("div");
      box.className = "error-message";
      fieldEl.closest(".form-group").appendChild(box);
    }
    box.textContent = msg;
    box.style.display = msg ? "block" : "none";
    if (msg) fieldEl.classList.add("invalid");
    else fieldEl.classList.remove("invalid");
  };

  const clearFeedback = (name) => {
    hideSuccess(name);
    const el = fields[name];
    if (!el) return;
    const box = el
      .closest(".form-group")
      ?.querySelector(".error-message:not(.django)");
    if (box) box.style.display = "none";
    el.classList.remove("invalid");
  };

  // Validaciones
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  function validateRUT(rut) {
    rut = rut.replace(/\./g, "").replace("-", "").toLowerCase();
    if (rut.length < 8 || rut.length > 9) return false;
    const body = rut.slice(0, -1);
    const dv = rut.slice(-1);
    if (!/^\d+$/.test(body)) return false;

    let sum = 0,
      mul = 2;
    for (let i = body.length - 1; i >= 0; i--) {
      sum += parseInt(body[i], 10) * mul;
      mul = mul === 7 ? 2 : mul + 1;
    }
    const res = 11 - (sum % 11);
    const calc = res === 11 ? "0" : res === 10 ? "k" : String(res);
    return dv === calc;
  }

  function checkPasswordStrength(password) {
    let score = 0;
    if (password.length >= 8) score++;
    if (password.length >= 12) score++;
    if (/[a-z]/.test(password)) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[0-9]/.test(password)) score++;
    if (/[^A-Za-z0-9]/.test(password)) score++;

    let strength = "",
      color = "";
    if (score < 3) {
      strength = "Muy débil";
      color = "#ef4444";
    } else if (score < 4) {
      strength = "Débil";
      color = "#f59e0b";
    } else if (score < 5) {
      strength = "Buena";
      color = "#10b981";
    } else {
      strength = "Muy fuerte";
      color = "#059669";
    }

    return { score, strength, color, percentage: (score / 6) * 100 };
  }

  function updatePasswordStrength() {
    const container = document.getElementById("password_strength");
    const fill = document.getElementById("strength_fill");
    const text = document.getElementById("strength_text");
    const val = fields.password1.value || "";
    if (!val) {
      container.style.display = "none";
      return;
    }
    const s = checkPasswordStrength(val);
    container.style.display = "block";
    fill.style.width = s.percentage + "%";
    fill.style.backgroundColor = s.color;
    text.textContent = s.strength;
    text.style.color = s.color;
  }

  function validateField(name) {
    const el = fields[name];
    const value = (el.value || "").trim();

    clearFeedback(name);

    switch (name) {
      case "first_name":
      case "last_name":
        if (!value)
          return (
            showError(
              el,
              `${name === "first_name" ? "Nombres" : "Apellidos"} es requerido`
            ),
            false
          );
        if (value.length < 2)
          return showError(el, "Debe tener al menos 2 caracteres"), false;
        if (!/^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/.test(value))
          return showError(el, "Solo se permiten letras y espacios"), false;
        showSuccess(name, "✓ Válido");
        return true;

      case "email":
        if (!value) return showError(el, "Email es requerido"), false;
        if (!emailRegex.test(value))
          return showError(el, "Formato de email inválido"), false;
        showSuccess(name, "✓ Email válido");
        return true;

      case "rut":
        if (!value) return showError(el, "RUT es requerido"), false;
        if (!validateRUT(value)) return showError(el, "RUT inválido"), false;
        showSuccess(name, "✓ RUT válido");
        return true;

      case "password1":
        updatePasswordStrength();
        if (!value) return showError(el, "Contraseña es requerida"), false;
        if (value.length < 8)
          return showError(el, "Debe tener al menos 8 caracteres"), false;
        if (checkPasswordStrength(value).score < 3)
          return showError(el, "Contraseña muy débil"), false;
        showSuccess(name, "✓ Contraseña segura");
        return true;

      case "password2":
        if (!value)
          return showError(el, "Confirmar contraseña es requerido"), false;
        if (value !== fields.password1.value)
          return showError(el, "Las contraseñas no coinciden"), false;
        showSuccess(name, "✓ Contraseñas coinciden");
        return true;
    }
    return true;
  }

  // Eventos en tiempo real
  Object.keys(fields).forEach((name) => {
    const el = fields[name];
    el.addEventListener("input", () => validateField(name));
    el.addEventListener("blur", () => validateField(name));
  });

  // Formateo de RUT on-input
  fields.rut.addEventListener("input", (e) => {
    let v = e.target.value.replace(/\D/g, "");
    if (v.length > 1) {
      const body = v.slice(0, -1);
      const dv = v.slice(-1);
      v = body.replace(/\B(?=(\d{3})+(?!\d))/g, ".") + "-" + dv;
    }
    e.target.value = v;
  });

  function validateForm() {
    return ["first_name", "last_name", "email", "rut", "password1", "password2"]
      .map(validateField)
      .every(Boolean);
  }

  form.addEventListener("submit", (e) => {
    // En producción, dejamos que Django procese el POST.
    // Solo evitamos el submit si las validaciones de front fallan.
    if (!validateForm()) {
      e.preventDefault();
      return false;
    }
    // Mostrar spinner mientras el form se envía (opcional)
    submitBtn.disabled = true;
    btnText.style.display = "none";
    loading.style.display = "block";
    // el submit continúa al servidor
  });

  // Al cargar, si hay errores de Django, muestra el indicador de fuerza si corresponde
  if (fields.password1.value) updatePasswordStrength();

  console.log("[registro_persona] listo");
});
