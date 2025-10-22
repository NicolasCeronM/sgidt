/* static/ayuda/js/chatbot.js */
(function () {
  const modal = document.getElementById('chatbotModal');
  const openBtn = document.getElementById('btnContactarSoporte');
  const messagesEl = document.getElementById('chatbotMessages');
  const suggestEl = document.getElementById('chatSuggest');
  const form = document.getElementById('chatbotForm');
  const input = document.getElementById('chatbotText');

  if (!modal || !form || !messagesEl || !input) return;

  const sendBtn = form.querySelector('button[type="submit"]');
  const STORAGE_KEY = 'sgidt.chat.history.v1';

  // ========================================================================
  // Helpers
  // ========================================================================

  const getCSRF = () => {
    const inp = form.querySelector('input[name="csrfmiddlewaretoken"]');
    if (inp?.value) return inp.value;
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? m[1] : '';
  };

  const escapeHTML = (s) =>
    (s || '').replace(/[&<>"']/g, (m) => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;',
    }[m]));

  // Markdown-lite: **bold**, listas (-/*), links, code blocks, saltos de línea
  const renderMarkdownLite = (md) => {
    if (!md) return '';
    let html = md;

    // 1) elimina encabezados markdown (# …)
    html = html.replace(/^\s*#{1,6}\s+/gm, '');

    // 2) code blocks ```...``` (escapamos el contenido)
    html = html.replace(/```([\s\S]*?)```/g, (m, code) =>
      `<pre><code>${escapeHTML(code)}</code></pre>`
    );

    // 3) escapar el resto
    html = escapeHTML(html);

    // 4) **bold**
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    // 5) [txt](url)
    html = html.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');

    // 6) linkify URLs simples que no vengan como markdown
    html = html.replace(/(?<!["'=])(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>');

    // 7) listas '- ' o '* '
    const lines = html.split(/\n/);
    let out = [];
    let inList = false;

    for (const ln of lines) {
      if (/^\s*[-*]\s+/.test(ln)) {
        if (!inList) {
          out.push('<ul>');
          inList = true;
        }
        out.push('<li>' + ln.replace(/^\s*[-*]\s+/, '') + '</li>');
      } else {
        if (inList) {
          out.push('</ul>');
          inList = false;
        }
        out.push(ln);
      }
    }
    if (inList) out.push('</ul>');

    // 8) párrafos/saltos
    html = out.join('\n')
      .replace(/\n{2,}/g, '</p><p>')
      .replace(/\n/g, '<br>');

    return '<p>' + html + '</p>';
  };

  const scrollToBottom = () => {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  };

  const addBubble = (text, who = 'bot') => {
    const div = document.createElement('div');
    div.className = `msg ${who}`;
    if (who === 'bot') div.innerHTML = renderMarkdownLite(text);
    else div.textContent = text;

    messagesEl.appendChild(div);
    saveHistory();
    scrollToBottom();
    return div;
  };

  const setTyping = (on) => {
    let typing = messagesEl.querySelector('.msg.typing');
    if (on && !typing) {
      typing = document.createElement('div');
      typing.className = 'msg bot typing';
      typing.setAttribute('aria-label', 'Escribiendo…');
      typing.innerHTML = '<span class="dots">Escribiendo…</span>';
      messagesEl.appendChild(typing);
      scrollToBottom();
    }
    if (!on && typing) typing.remove();
  };

  const renderChips = (arr) => {
    suggestEl.innerHTML = '';
    if (!arr || !arr.length) return;

    arr.slice(0, 6).forEach((txt) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'chip';
      b.textContent = txt;
      b.addEventListener('click', () => {
        input.value = txt;
        form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
      });
      suggestEl.appendChild(b);
    });
  };

  const setSending = (sending) => {
    if (!sendBtn) return;
    sendBtn.disabled = sending;
    sendBtn.setAttribute('aria-busy', sending ? 'true' : 'false');
  };

  // ========================================================================
  // Persistencia de conversación
  // ========================================================================

  const saveHistory = () => {
    const items = Array.from(messagesEl.querySelectorAll('.msg')).map((el) => ({
      who: el.classList.contains('user') ? 'user' : 'bot',
      html: el.classList.contains('bot') ? el.innerHTML : escapeHTML(el.textContent || ''),
    }));
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  };

  const restoreHistory = () => {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return false;
    try {
      const items = JSON.parse(raw);
      messagesEl.innerHTML = '';

      for (const it of items) {
        const div = document.createElement('div');
        div.className = `msg ${it.who}`;
        if (it.who === 'bot') {
          div.innerHTML = it.html;
        } else {
          div.textContent = it.html
            ? it.html.replace(/&lt;|&gt;|&amp;|&quot;|&#39;/g, (m) => ({
              '&lt;': '<',
              '&gt;': '>',
              '&amp;': '&',
              '&quot;': '"',
              '&#39;': "'",
            }[m]))
            : '';
        }
        messagesEl.appendChild(div);
      }
      scrollToBottom();
      return true;
    } catch {
      return false;
    }
  };

  // ========================================================================
  // Accesibilidad / Modal
  // ========================================================================

  const focusable = () =>
    modal.querySelectorAll('a,button,input,textarea,[tabindex]:not([tabindex="-1"])');

  const trapFocus = (e) => {
    if (modal.getAttribute('aria-hidden') === 'true') return;

    const els = Array.from(focusable()).filter((el) => !el.hasAttribute('disabled'));
    if (els.length === 0) return;

    const first = els[0];
    const last = els[els.length - 1];

    if (e.key === 'Tab') {
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    } else if (e.key === 'Escape') {
      closeModal();
    }
  };

  const openModal = () => {
    modal.setAttribute('aria-hidden', 'false');
    document.body.classList.add('no-scroll');
    setTimeout(() => input.focus(), 50);
  };

  const closeModal = () => {
    modal.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('no-scroll');
  };

  // ========================================================================
  // Petición AJAX segura
  // ========================================================================

  const fetchWithTimeout = (url, opts = {}, timeoutMs = 25000) =>
    Promise.race([
      fetch(url, opts),
      new Promise((_, rej) => setTimeout(() => rej(new Error('timeout')), timeoutMs)),
    ]);

  const ask = async (msg) => {
    const endpoint = form.dataset.endpoint;
    const csrf = getCSRF();

    try {
      setSending(true);
      setTyping(true);

      const res = await fetchWithTimeout(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': csrf,
        },
        body: JSON.stringify({ message: msg }),
      });

      let data = {};
      try {
        data = await res.json();
      } catch {
        data = {};
      }

      setTyping(false);
      setSending(false);

      // Manejo de estados
      if (res.status === 429) {
        addBubble(data?.reply || 'Estás enviando muy rápido 😅. Intenta de nuevo en un momento.');
        return;
      }
      if (res.status === 401 || res.status === 403) {
        addBubble('No autorizado. Refresca la página para renovar tu sesión o CSRF.');
        return;
      }
      if (res.status === 413) {
        addBubble('Mensaje demasiado largo. Intenta resumir tu consulta.');
        return;
      }
      if (!res.ok) {
        addBubble(data?.reply || 'Hubo un problema procesando tu mensaje. Intenta nuevamente.');
        return;
      }

      addBubble(data.reply || 'Sin respuesta.');
      renderChips(data.suggest || []);
    } catch (e) {
      setTyping(false);
      setSending(false);
      addBubble(
        e?.message === 'timeout'
          ? 'El servidor tardó demasiado ⏳. Intenta otra vez.'
          : 'Error de conexión. Revisa tu red e intenta otra vez.'
      );
      console.error(e);
    }
  };

  // ========================================================================
  // Eventos
  // ========================================================================

  if (openBtn) {
    openBtn.addEventListener('click', (e) => {
      e.preventDefault();
      openModal();
    });
  }

  // abrir con hash #contactar-soporte
  if (location.hash === '#contactar-soporte') openModal();

  modal.addEventListener('click', (e) => {
    if (e.target.dataset.close === 'true') closeModal();
  });

  document.addEventListener('keydown', trapFocus);

  // enviar: Enter; salto de línea: Shift+Enter
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
    }
  });

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    if (sendBtn?.disabled) return; // evita doble envío
    const text = (input.value || '').trim();
    if (!text) return;
    addBubble(text, 'user');
    input.value = '';
    ask(text);
  });

  // ========================================================================
  // Inicialización
  // ========================================================================

  if (!restoreHistory()) {
    renderChips(['Conectar Google Drive', 'Subir un PDF', 'Validación con SII', 'Cambiar datos de la empresa']);
  }
})();
