/**
 * Session Guard — Auto-logout por inactividad
 * ============================================
 * Desloguea al usuario después de INACTIVITY_MINUTES sin actividad.
 * Muestra una advertencia WARNING_BEFORE_MINUTES antes de expirar.
 *
 * Uso: importar e invocar initSessionGuard() en cualquier página protegida.
 */

const INACTIVITY_MINUTES = 30;   // minutos sin actividad → logout
const WARNING_BEFORE_MINUTES = 2; // minutos antes de expirar → mostrar aviso

const INACTIVITY_MS = INACTIVITY_MINUTES * 60 * 1000;
const WARNING_MS    = WARNING_BEFORE_MINUTES * 60 * 1000;

let _inactivityTimer  = null;
let _warningTimer     = null;
let _warningEl        = null;
let _countdownInterval = null;

/** Limpia localStorage y cookies de sesión, redirige a /login */
function _doLogout(reason = 'inactividad') {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  // Borrar cookies (por si las páginas SSR las usan)
  document.cookie = 'token=; Max-Age=0; path=/';
  document.cookie = 'user=; Max-Age=0; path=/';
  window.location.href = `/login?expired=1&reason=${reason}`;
}

/** Crea / muestra el banner de advertencia con cuenta regresiva */
function _showWarning() {
  if (_warningEl) return; // ya visible

  _warningEl = document.createElement('div');
  _warningEl.id = 'session-warning';
  _warningEl.innerHTML = `
    <div style="
      position:fixed;bottom:1.5rem;right:1.5rem;z-index:99999;
      background:#1e3a5f;color:white;
      padding:1rem 1.25rem;border-radius:12px;
      box-shadow:0 8px 32px rgba(0,0,0,0.35);
      max-width:320px;font-size:0.875rem;line-height:1.5;
      border:1.5px solid #3b82f6;
    ">
      <div style="font-weight:700;margin-bottom:0.35rem">⏱️ Sesión por expirar</div>
      <div>Tu sesión cerrará en <strong id="sg-countdown"></strong> por inactividad.</div>
      <div style="margin-top:0.75rem;display:flex;gap:0.5rem">
        <button id="sg-stay" style="
          flex:1;background:#2563eb;color:white;border:none;
          border-radius:6px;padding:6px 12px;cursor:pointer;
          font-weight:600;font-size:0.8rem;
        ">Continuar sesión</button>
        <button id="sg-logout" style="
          flex:1;background:transparent;color:#93c5fd;border:1.5px solid #3b82f6;
          border-radius:6px;padding:6px 12px;cursor:pointer;
          font-weight:600;font-size:0.8rem;
        ">Cerrar sesión</button>
      </div>
    </div>`;

  document.body.appendChild(_warningEl);

  document.getElementById('sg-stay')?.addEventListener('click', _resetTimers);
  document.getElementById('sg-logout')?.addEventListener('click', () => _doLogout('manual'));

  // Cuenta regresiva visual
  let secondsLeft = WARNING_BEFORE_MINUTES * 60;
  const el = document.getElementById('sg-countdown');
  const tick = () => {
    if (el) el.textContent = secondsLeft > 60
      ? `${Math.ceil(secondsLeft / 60)} min`
      : `${secondsLeft}s`;
    secondsLeft--;
  };
  tick();
  _countdownInterval = setInterval(tick, 1000);
}

function _hideWarning() {
  if (_warningEl) {
    _warningEl.remove();
    _warningEl = null;
  }
  if (_countdownInterval) {
    clearInterval(_countdownInterval);
    _countdownInterval = null;
  }
}

/** Reinicia todos los temporizadores (se llama en cada evento de actividad) */
function _resetTimers() {
  _hideWarning();
  clearTimeout(_inactivityTimer);
  clearTimeout(_warningTimer);

  // Advertencia: INACTIVITY_MS - WARNING_MS antes del logout
  _warningTimer = setTimeout(_showWarning, INACTIVITY_MS - WARNING_MS);
  // Logout definitivo
  _inactivityTimer = setTimeout(() => _doLogout('inactividad'), INACTIVITY_MS);
}

/** Inicializa el guard. Llamar una vez por página protegida. */
export function initSessionGuard() {
  // Solo activar si hay sesión activa
  const token = localStorage.getItem('token');
  if (!token) return;

  const EVENTS = ['mousemove', 'mousedown', 'keypress', 'touchstart', 'scroll', 'click'];
  EVENTS.forEach(ev => window.addEventListener(ev, _resetTimers, { passive: true }));

  // Sincronización entre pestañas: si otra pestaña hace logout, esta también
  window.addEventListener('storage', (e) => {
    if (e.key === 'token' && !e.newValue) {
      window.location.href = '/login?expired=1&reason=otra_pestana';
    }
  });

  _resetTimers(); // arrancar temporizadores
}

/** Muestra un aviso en el login si la sesión expiró */
export function checkExpiredSession() {
  const params = new URLSearchParams(window.location.search);
  if (params.get('expired') === '1') {
    const reason = params.get('reason') || 'inactividad';
    const msgs = {
      inactividad: 'Tu sesión cerró por inactividad.',
      manual: 'Has cerrado sesión correctamente.',
      otra_pestana: 'Tu sesión cerró en otra pestaña.',
    };
    const msg = msgs[reason] || msgs.inactividad;

    const banner = document.createElement('div');
    banner.innerHTML = `
      <div style="
        background:#fef3c7;border:1.5px solid #f59e0b;color:#92400e;
        padding:0.75rem 1rem;border-radius:8px;font-size:0.85rem;
        font-weight:600;margin-bottom:1rem;text-align:center;
      ">⏱️ ${msg}</div>`;
    const form = document.querySelector('form') || document.body.firstElementChild;
    if (form) form.insertAdjacentElement('beforebegin', banner.firstElementChild);

    // Limpiar URL
    window.history.replaceState({}, '', '/login');
  }
}
