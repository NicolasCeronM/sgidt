(function () {
  const openBtn  = document.getElementById('btnContactarSoporte');
  const modal    = document.getElementById('chatbotModal');
  const form     = document.getElementById('chatbotForm');
  const input    = document.getElementById('chatbotText');
  const messages = document.getElementById('chatbotMessages');
  if (!openBtn || !modal || !form || !input || !messages) return;

  // Lock scroll fondo cuando el modal está abierto
  const lockScroll = (on) => {
    document.documentElement.style.overflow = on ? 'hidden' : '';
    document.body.style.overflow = on ? 'hidden' : '';
  };

  // Abrir / Cerrar
  openBtn.addEventListener('click', (e) => {
    e.preventDefault();
    modal.classList.add('active');
    lockScroll(true);
    setTimeout(() => input.focus(), 0);
  });
  modal.addEventListener('click', (e) => {
    if (e.target.dataset.close === 'true') {
      modal.classList.remove('active');
      lockScroll(false);
    }
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal.classList.contains('active')) {
      modal.classList.remove('active');
      lockScroll(false);
    }
  });

  // CSRF (Django)
  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
  }
  const csrftoken = getCookie('csrftoken');

  // Util: scroll al final
  function scrollBottom(){ messages.scrollTop = messages.scrollHeight; }

  // Render markdown simple: **negrita** y links
  function renderMD(text){
    let t = text
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>')
      .replace(/\n/g, '<br>');
    return t;
  }

  // Pinta burbuja
  function pushMsg(text, who = 'user') {
    const div = document.createElement('div');
    div.className = `msg ${who}`;
    div.innerHTML = renderMD(text) + `<span class="meta">${new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}</span>`;
    messages.appendChild(div);
    scrollBottom();
  }

  // “Escribiendo…” animado
  function showTyping(on=true){
    let t = document.getElementById('botTyping');
    if(on){
      if(!t){
        t = document.createElement('div');
        t.id = 'botTyping';
        t.className = 'msg bot typing';
        t.innerHTML = `
          <span>Escribiendo</span>
          <span class="typing-dots"><i></i><i></i><i></i></span>
        `;
        messages.appendChild(t);
      }
    } else if(t){ t.remove(); }
    scrollBottom();
  }

  // Chips de sugerencia
  function renderSuggest(list){
    const wrapId = 'chatSuggest';
    let wrap = document.getElementById(wrapId);
    if(!list || !list.length){ if(wrap) wrap.remove(); return; }
    if(!wrap){
      wrap = document.createElement('div');
      wrap.id = wrapId;
      wrap.style.display = 'flex';
      wrap.style.flexWrap = 'wrap';
      wrap.style.gap = '6px';
      messages.appendChild(wrap);
    } else {
      wrap.innerHTML = '';
    }
    list.forEach(txt => {
      const b = document.createElement('button');
      b.type = 'button';
      b.textContent = txt;
      b.className = 'chip-suggest';
      b.onclick = () => { input.value = txt; form.dispatchEvent(new Event('submit')); };
      wrap.appendChild(b);
    });
    scrollBottom();
  }

  // Enviar 
  input.addEventListener('keydown', (e) => {
    if(e.key === 'Enter' && !e.shiftKey){
      e.preventDefault();
      form.requestSubmit();
    }
  });

  form.addEventListener('submit', async function (e) {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    pushMsg(text, 'user');
    input.value = '';

    showTyping(true);
    try {
      const res = await fetch(form.dataset.endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrftoken || ''
        },
        body: JSON.stringify({ message: text })
      });
      const data = await res.json();
      showTyping(false);
      pushMsg(data.reply || 'Lo siento, no pude procesar tu solicitud.', 'bot');
      renderSuggest(data.suggest || []);
    } catch {
      showTyping(false);
      pushMsg('Error de red. Intenta nuevamente.', 'bot');
    }
  });
})();
