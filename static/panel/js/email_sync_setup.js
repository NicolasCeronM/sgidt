document.addEventListener('DOMContentLoaded', () => {
    console.log("🔄 1. Script de configuración de correo INICIADO");

    // 1. Referencias
    const modal = document.getElementById('email-sync-modal');
    console.log("🔍 2. Buscando modal...", modal ? "ENCONTRADO ✅" : "NO ENCONTRADO ❌");
    
    if (!modal) {
        console.error("⛔ El script se detuvo porque no hay modal en el HTML.");
        return; 
    }

    const openModalButton = document.getElementById('open-email-sync-modal-btn');
    console.log("🔍 3. Buscando botón 'Configurar'...", openModalButton ? "ENCONTRADO ✅" : "NO ENCONTRADO ❌ (Revisa el ID en _integraciones.html)");

    const form = document.getElementById('email-sync-form');
    const emailOptions = document.getElementById('email-options');
    const otherEmailInput = document.getElementById('other-email');
    const skipButton = document.getElementById('email-sync-skip');
    const closeButton = document.getElementById('email-sync-close');

    // 2. Lógica del botón
    if (openModalButton) {
        openModalButton.addEventListener('click', (event) => {
            event.preventDefault();
            console.log("🖱️ 4. ¡CLICK DETECTADO! Intentando abrir modal...");
            modal.style.display = 'flex'; 
            console.log("✨ Modal debería ser visible ahora (display: flex)");
        });
    }

    // 3. Lógica de cierre
    const lastSkippedKey = 'emailSyncLastSkipped';
    const twentyFourHours = 24 * 60 * 60 * 1000;

    const skipModal = () => {
        const now = new Date().getTime();
        localStorage.setItem(lastSkippedKey, now.toString());
        modal.style.display = 'none';
    };

    if (skipButton) skipButton.addEventListener('click', skipModal);
    if (closeButton) closeButton.addEventListener('click', () => { modal.style.display = 'none'; });

    // 4. Inputs
    if (emailOptions) {
        emailOptions.addEventListener('change', () => {
            if (emailOptions.value === 'other') {
                otherEmailInput.style.display = 'block';
                otherEmailInput.required = true;
            } else {
                otherEmailInput.style.display = 'none';
                otherEmailInput.required = false;
            }
        });
    }

    // 5. Check automático
    fetch('/panel/api/check-email-sync-status/')
        .then(response => response.json())
        .then(data => {
            console.log("📡 API Status Check:", data);
            if (data.is_configured) return;

            const lastSkippedTimestamp = localStorage.getItem(lastSkippedKey);
            const now = new Date().getTime();

            if (!lastSkippedTimestamp || (now - parseInt(lastSkippedTimestamp)) > twentyFourHours) {
                console.log("⏰ Abriendo modal automáticamente (tiempo cumplido)");
                modal.style.display = 'flex';
            }
        })
        .catch(error => console.error('Error check status:', error));

    // 6. Submit
    if (form) {
        form.addEventListener('submit', (event) => {
            event.preventDefault();
            const formData = new FormData(form);
            
            const emailUser = formData.get('email_user') === 'other' 
                ? formData.get('other_email_user') 
                : formData.get('email_user');
            
            const data = {
                email_user: emailUser,
                provider: formData.get('provider'),
                password: formData.get('password'),
            };

            let csrfToken = '';
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                const [name, value] = cookie.trim().split('=');
                if (name === 'csrftoken') {
                    csrfToken = value;
                    break;
                }
            }

            fetch('/panel/api/save-email-sync-config/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify(data),
            })
            .then(response => response.json())
            .then(result => {
                if (result.status === 'success') {
                    alert('¡Configuración guardada con éxito!');
                    modal.style.display = 'none';

                    window.location.reload();
                } else {
                    alert('Error: ' + result.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error inesperado al guardar.');
            });
        });
    }
});