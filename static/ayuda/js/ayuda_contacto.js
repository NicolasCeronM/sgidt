(function () {
  const form = document.getElementById("helpContactForm");
  if (!form) return;

  // Función para obtener el token CSRF de Django
  const getCsrf = () =>
    (document.querySelector('input[name="csrfmiddlewaretoken"]') || {}).value ||
    "";

  form.addEventListener("submit", async (e) => {
    e.preventDefault(); // Evita la recarga de la página

    const btn = form.querySelector('button[type="submit"]');
    const original = btn.innerHTML;

    // 1. Cambiar botón a estado "Cargando"
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Enviando...';

    try {
      // 2. Enviar petición AJAX al servidor
      const res = await fetch(form.action, {
        method: "POST",
        headers: {
          "X-Requested-With": "XMLHttpRequest", // Importante para que Django sepa que es AJAX
          "X-CSRFToken": getCsrf(),
        },
        body: new FormData(form),
      });

      // 3. Manejar respuesta
      if (res.ok) {
        // --- ÉXITO ---
        form.reset(); // Limpiar el formulario

        // Mostrar alerta bonita con SweetAlert2
        Swal.fire({
          title: "¡Mensaje Enviado!",
          text: "Tu mensaje de ayuda ha sido enviado correctamente. Te contactaremos pronto.",
          icon: "success",
          confirmButtonColor: "#27ae60", // Tu verde corporativo
          confirmButtonText: "Aceptar",
          timer: 5000, // Se cierra automático en 5 seg
          timerProgressBar: true,
        });

      } else {
        // --- ERROR DEL SERVIDOR (Ej: validación fallida) ---
        console.warn("No se pudo enviar el mensaje (HTTP " + res.status + ")");
        
        Swal.fire({
          title: "Error",
          text: "Hubo un problema al enviar el mensaje. Por favor, revisa los campos e intenta nuevamente.",
          icon: "error",
          confirmButtonColor: "#e74c3c", // Rojo error
          confirmButtonText: "Cerrar"
        });
      }

    } catch (err) {
      // --- ERROR DE RED (Ej: sin internet) ---
      console.error("Error de red:", err);
      
      Swal.fire({
        title: "Error de conexión",
        text: "No pudimos conectar con el servidor. Verifica tu conexión a internet.",
        icon: "error",
        confirmButtonColor: "#e74c3c",
        confirmButtonText: "Cerrar"
      });

    } finally {
      // 4. Restaurar botón a estado original
      btn.disabled = false;
      btn.innerHTML = original;
    }
  });
})();