/**
 * Middleware de Astro — Seguridad y alias de rutas
 * ================================================
 * 1. Alias de rutas: oculta los nombres reales de páginas internas.
 * 2. Protección SSR: redirige a /login si no hay cookie de sesión.
 * 3. Cabeceras de seguridad en todas las respuestas.
 */
import { defineMiddleware } from 'astro:middleware';

// ── Alias públicos → rutas reales ──────────────────────────────────────────
// Los usuarios verán /panel, /gestion, etc. en lugar de los nombres reales.
// Agrega aquí tantos alias como necesites.
const ROUTE_ALIASES: Record<string, string> = {
  '/panel':        '/dashboard-admin',
  '/mi-panel':     '/dashboard-empleado',
  '/gestion':      '/inventario',
  '/equipo':       '/empleados',
  '/compras-proveedor': '/compras',
  '/experto':      '/sistema-experto',
  '/catalogo-interno': '/catalogo-admin',
  '/mis-ventas':   '/ventas',
  '/mis-pedidos':  '/mis-compras',
  '/recomendaciones-ia': '/recomendaciones',
};

// ── Rutas que requieren autenticación (prefijos) ───────────────────────────
const PROTECTED_PREFIXES = [
  '/dashboard-admin',
  '/dashboard-empleado',
  '/inventario',
  '/empleados',
  '/compras',
  '/sistema-experto',
  '/catalogo-admin',
  '/ventas',
  '/mis-compras',
  '/recomendaciones',
  '/factura',
  // Aliases también protegidos
  '/panel',
  '/mi-panel',
  '/gestion',
  '/equipo',
  '/compras-proveedor',
  '/experto',
  '/catalogo-interno',
  '/mis-ventas',
  '/mis-pedidos',
  '/recomendaciones-ia',
];

export const onRequest = defineMiddleware(async (context, next) => {
  const { url, cookies, redirect } = context;
  const pathname = url.pathname;

  // ── 1. Resolver alias de ruta ────────────────────────────────────────────
  const aliasTarget = ROUTE_ALIASES[pathname];
  if (aliasTarget) {
    // Reescribir internamente: mantener la URL del alias en el navegador
    // pero servir la página real. En Astro SSR esto se hace con rewrite.
    // Si no tienes SSR habilitado, usa redirect temporal.
    return redirect(aliasTarget, 302);
  }

  // ── 2. Protección de rutas autenticadas ──────────────────────────────────
  const isProtected = PROTECTED_PREFIXES.some(p => pathname.startsWith(p));
  if (isProtected) {
    const token = cookies.get('token')?.value;
    if (!token) {
      return redirect('/login?expired=1&reason=no_sesion', 302);
    }
  }

  // ── 3. Ejecutar handler normal ───────────────────────────────────────────
  const response = await next();

  // ── 4. Cabeceras de seguridad en respuestas HTML ─────────────────────────
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('text/html')) {
    response.headers.set('X-Frame-Options', 'DENY');
    response.headers.set('X-Content-Type-Options', 'nosniff');
    response.headers.set('X-XSS-Protection', '1; mode=block');
    response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
    response.headers.set('Permissions-Policy', 'geolocation=(), microphone=(), camera=()');
  }

  return response;
});
