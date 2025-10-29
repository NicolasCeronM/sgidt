document.addEventListener('DOMContentLoaded', () => {

    const modal = document.getElementById('email-sync-modal');
    if (!modal) return; // Exit if the modal is not on the page

    const form = document.getElementById('email-sync-form');
    const emailOptions = document.getElementById('email-options');
    const otherEmailInput = document.getElementById('other-email');
    const skipButton = document.getElementById('email-sync-skip');
    const closeButton = document.getElementById('email-sync-close');

    const lastSkippedKey = 'emailSyncLastSkipped';
    const twentyFourHours = 24 * 60 * 60 * 1000; // 24 hours in milliseconds

    // Function to handle skipping the modal
    const skipModal = () => {
        const now = new Date().getTime();
        localStorage.setItem(lastSkippedKey, now.toString());
        modal.style.display = 'none';
    };

    // Attach skip logic to both the skip and close buttons
    skipButton.addEventListener('click', skipModal);
    closeButton.addEventListener('click', skipModal);

    // 1. Check if the modal should be shown
    fetch('/panel/api/check-email-sync-status/')
        .then(response => response.json())
        .then(data => {
            // Only proceed if the email is NOT configured
            if (data.is_configured) {
                return; 
            }

            const lastSkippedTimestamp = localStorage.getItem(lastSkippedKey);
            const now = new Date().getTime();

            // Show the modal if:
            // - It has never been skipped before OR
            // - More than 24 hours have passed since it was last skipped
            if (!lastSkippedTimestamp || (now - parseInt(lastSkippedTimestamp)) > twentyFourHours) {
                modal.style.display = 'flex';
            }
        })
        .catch(error => console.error('Error al verificar el estado del correo:', error));

    // 2. Lógica para mostrar el campo de "otro correo"
    emailOptions.addEventListener('change', () => {
        if (emailOptions.value === 'other') {
            otherEmailInput.style.display = 'block';
            otherEmailInput.required = true;
        } else {
            otherEmailInput.style.display = 'none';
            otherEmailInput.required = false;
        }
    });

    // 3. Manejar el envío del formulario (this part remains the same)
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

        const csrfToken = document.cookie.split('; ').find(row => row.startsWith('csrftoken=')).split('=')[1];

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
            } else {
                alert('Error: ' + result.message);
            }
        })
        .catch(error => {
            console.error('Error al guardar la configuración:', error);
            alert('Ocurrió un error inesperado. Revisa la consola para más detalles.');
        });
    });
});