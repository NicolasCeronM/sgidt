(function () {
  const fab   = document.getElementById('chatFab');
  const panel = document.getElementById('chatPanel');
  const close = document.getElementById('chatClose');
  const body  = document.getElementById('chatBody');
  const form  = document.getElementById('chatForm');
  const input = document.getElementById('chatInput');
  const endpoint = form?.dataset?.endpoint;

  if (!fab || !panel || !form) return; // por si no está en otras vistas

  function openPanel(){
    panel.hidden = false;
    localStorage.setItem('sgidt_chat_open','1');
    setTimeout(() => input?.focus(), 0);
  }
  function closePanel(){
    panel.hidden = true;
    localStorage.setItem('sgidt_chat_open','0');
  }

  // Restaurar estado
  if (localStorage.getItem('sgidt_chat_open') === '1') panel.hidden = false;

  fab.addEventListener('click', () => panel.hidden ? openPanel() : closePanel());
  close.addEventListener('click', closePanel);
  document.addEventListener('keydown', (e)=>{ if(e.key==='Escape' && !panel.hidden) closePanel(); });

  // Envío al backend Django (espera JSON {reply: "..."} )
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;

    const u = document.createElement('div');
    u.className = 'msg user';
    u.innerHTML = `<p>${text}</p>`;
    body.appendChild(u);
    input.value = '';
    body.scrollTop = body.scrollHeight;

    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        body: new FormData(form)
      });
      const data = await res.json();
      const b = document.createElement('div');
      b.className = 'msg bot';
      b.innerHTML = `<p>${(data.reply || 'Gracias, en un momento te respondo. 🤖')}</p>`;
      body.appendChild(b);
    } catch (err) {
      const b = document.createElement('div');
      b.className = 'msg bot';
      b.innerHTML = `<p>No pude enviar el mensaje. Intenta de nuevo.</p>`;
      body.appendChild(b);
    }
    body.scrollTop = body.scrollHeight;
  });
})();
