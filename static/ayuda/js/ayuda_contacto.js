(function () {
  const form = document.getElementById("helpContactForm");
  if (!form) return;

  // Obtener CSRF
  const getCsrf = () =>
    (document.querySelector('input[name="csrfmiddlewaretoken"]') || {}).value ||
    "";

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const btn = form.querySelector('button[type="submit"]');
    const original = btn.innerHTML;

    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Enviando...';

    try {
      const res = await fetch(form.action, {
        method: "POST",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": getCsrf(),
        },
        body: new FormData(form),
      });

      if (res.ok) {
        form.reset();
      } else {
        console.warn("No se pudo enviar el mensaje (HTTP " + res.status + ")");
      }
    } catch (err) {
      console.error("Error de red:", err);
    } finally {
      btn.disabled = false;
      btn.innerHTML = original;
    }
  });
})();
