document.getElementById("loginForm").addEventListener("submit", function (e) {
  e.preventDefault();

  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;
  const errorMessage = document.getElementById("errorMessage");

  // Simulación de validación (aquí conectarías con tu backend)
  if (email === "demo@sgidt.com" && password === "demo123") {
    alert("¡Inicio de sesión exitoso! Redirigiendo al dashboard...");
    // Aquí redirigirias al dashboard
    // window.location.href = 'dashboard.html';
  } else {
    errorMessage.style.display = "block";
    setTimeout(() => {
      errorMessage.style.display = "none";
    }, 5000);
  }
});

// Ocultar mensaje de error al escribir
document.getElementById("email").addEventListener("input", function () {
  document.getElementById("errorMessage").style.display = "none";
});

document.getElementById("password").addEventListener("input", function () {
  document.getElementById("errorMessage").style.display = "none";
});
