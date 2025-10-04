(function () {
  const openBtn  = document.getElementById('btnContactarSoporte'); 
  const fabBtn   = document.getElementById('chatFab');             
  const modal    = document.getElementById('chatbotModal');
  const form     = document.getElementById('chatbotForm');
  const input    = document.getElementById('chatbotText');
  const messages = document.getElementById('chatbotMessages');
  const suggest  = document.getElementById('chatSuggest');

  // Si falta lo esencial del chat, salimos
  if (!modal || !form || !input || !messages) return;

  // Bloquear scroll del fondo cuando el modal está abierto
  const lockScroll = (on) => {
    document.documentElement.style.overflow = on ? 'hidden' : '';
    document.body.style.overflow = on ? 'hidden' : '';
  };

  // Scroll hasta el final
  function scrollBottom(){
    const go = () => { messages.scrollTop = messages.scrollHeight; };
    go(); requestAnimationFrame(go); setTimeout(go, 60);
  }

  // Abrir y cerrar el chat
  function openModal() {
    modal.classList.add('active');
    modal.setAttribute('aria-hidden', 'false');
    lockScroll(true);
    requestAnimationFrame(() => { input.focus(); scrollBottom(); });
  }
  function closeModal() {
    modal.classList.remove('active');
    modal.setAttribute('aria-hidden', 'true');
    lockScroll(false);
  }

  // Abrir desde el botón de la página
  if (openBtn) {
    openBtn.addEventListener('click', (e) => { e.preventDefault(); openModal(); });
  }
  // Abrir desde el FAB global 
  if (fabBtn){
    const fresh = fabBtn.cloneNode(true);
    fabBtn.replaceWith(fresh);
    fresh.addEventListener('click', (e) => { e.preventDefault(); openModal(); });
  }

  // Cerrar con backdrop o botón X
  modal.addEventListener('click', (e) => {
    if (e.target.dataset.close === 'true') closeModal();
  });
  const btnClose = modal.querySelector('.chatbot-close');
  btnClose?.addEventListener('click', closeModal);

  // Envío del formulario
  function renderMD(text){
    return text
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>')
      .replace(/\n/g, '<br>');
  }
  function pushMsg(text, who = 'user') {
    const div = document.createElement('div');
    div.className = `msg ${who}`;
    const now = new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
    div.innerHTML = renderMD(text) + `<span class="meta">${now}</span>`;
    messages.appendChild(div);
    scrollBottom();
  }
  function showTyping(on=true){
    let t = document.getElementById('botTyping');
    if (on && !t) {
      t = document.createElement('div');
      t.id = 'botTyping';
      t.className = 'msg bot small';
      t.textContent = 'Escribiendo…';
      messages.appendChild(t);
      scrollBottom();
    } else if (!on && t) {
      t.remove();
    }
  }
  function renderSuggest(items){
    suggest.innerHTML = '';
    (items || []).slice(0,6).forEach(txt => {
      const b = document.createElement('button');
      b.type = 'button'; b.className = 'chip-suggest'; b.textContent = txt;
      b.addEventListener('click', () => {
        input.value = txt;
        form.dispatchEvent(new Event('submit', {cancelable:true, bubbles:true}));
      });
      suggest.appendChild(b);
    });
  }
  function getCookie(name) {
    const value = `; ${document.cookie}`; const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
  }
  const csrftoken = getCookie('csrftoken');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    pushMsg(text, 'user');
    input.value = '';
    showTyping(true);
    try {
      const res = await fetch(form.dataset.endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken || '' },
        body: JSON.stringify({ message: text })
      });
      const data = await res.json();
      showTyping(false);
      pushMsg(data.reply || 'Lo siento, no pude procesar tu solicitud.', 'bot');
      renderSuggest(data.suggest || []);
    } catch (err) {
      showTyping(false);
      pushMsg('Error de red. Intenta nuevamente.', 'bot');
    }
  });

  window.addEventListener('resize', () => { if (modal.classList.contains('active')) scrollBottom(); });
})();

