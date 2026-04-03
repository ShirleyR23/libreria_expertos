"""
Servicio de Email - Gmail SMTP con templates HTML.
Envía correos transaccionales con diseño profesional.
"""
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
from datetime import datetime

from app.core.config import get_settings

settings = get_settings()


# ─── BASE TEMPLATE ────────────────────────────────────────────────────────────

def _base_template(content_html: str, preheader: str = "") -> str:
    """Envuelve el contenido en el template base de email."""
    year = datetime.now().year
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Librería</title>
<!--[if mso]><noscript><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml></noscript><![endif]-->
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background-color:#F4F1EC; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif; color:#2C2416; -webkit-text-size-adjust:100%; }}
  .wrapper {{ width:100%; background:#F4F1EC; padding:40px 16px; }}
  .container {{ max-width:580px; margin:0 auto; }}
  .header {{ background:#1A120B; border-radius:16px 16px 0 0; padding:32px 40px; text-align:center; }}
  .header-logo {{ font-size:28px; font-weight:700; color:#F5E6C8; letter-spacing:-0.5px; }}
  .header-logo span {{ color:#C9A96E; }}
  .header-tagline {{ font-size:13px; color:#8B7355; margin-top:4px; letter-spacing:1px; text-transform:uppercase; }}
  .body {{ background:#FFFFFF; padding:40px 40px 32px; }}
  .greeting {{ font-size:22px; font-weight:600; color:#1A120B; margin-bottom:8px; }}
  .divider {{ width:48px; height:3px; background:#C9A96E; border-radius:2px; margin:20px 0; }}
  .text {{ font-size:15px; line-height:1.7; color:#4A3728; margin-bottom:16px; }}
  .btn-wrap {{ text-align:center; margin:32px 0; }}
  .btn {{ display:inline-block; background:#1A120B; color:#F5E6C8 !important; text-decoration:none; padding:14px 36px; border-radius:8px; font-size:15px; font-weight:600; letter-spacing:0.3px; }}
  .btn:hover {{ background:#2C2416; }}
  .highlight-box {{ background:#FBF7F0; border:1px solid #E8D9C0; border-left:4px solid #C9A96E; border-radius:8px; padding:20px 24px; margin:24px 0; }}
  .highlight-box .label {{ font-size:11px; text-transform:uppercase; letter-spacing:1.5px; color:#8B7355; font-weight:600; margin-bottom:4px; }}
  .highlight-box .value {{ font-size:20px; font-weight:700; color:#1A120B; }}
  .table {{ width:100%; border-collapse:collapse; margin:20px 0; }}
  .table th {{ background:#F4F1EC; text-align:left; padding:10px 14px; font-size:12px; text-transform:uppercase; letter-spacing:1px; color:#8B7355; font-weight:600; }}
  .table td {{ padding:12px 14px; font-size:14px; border-bottom:1px solid #F4F1EC; color:#2C2416; }}
  .table tr:last-child td {{ border-bottom:none; }}
  .table .total-row td {{ font-weight:700; font-size:16px; border-top:2px solid #E8D9C0; padding-top:16px; }}
  .badge {{ display:inline-block; padding:4px 12px; border-radius:20px; font-size:12px; font-weight:600; }}
  .badge-success {{ background:#D1FAE5; color:#065F46; }}
  .badge-warning {{ background:#FEF3C7; color:#92400E; }}
  .footer {{ background:#1A120B; border-radius:0 0 16px 16px; padding:28px 40px; text-align:center; }}
  .footer p {{ font-size:12px; color:#8B7355; line-height:1.8; }}
  .footer a {{ color:#C9A96E; text-decoration:none; }}
  .social {{ margin:16px 0 0; }}
  .note {{ font-size:12px; color:#8B7355; margin-top:24px; padding-top:20px; border-top:1px solid #F4F1EC; }}
</style>
</head>
<body>
<span style="display:none;max-height:0;overflow:hidden;">{preheader}</span>
<div class="wrapper">
  <div class="container">
    <div class="header">
      <div class="header-logo">📚 Li<span>brer</span>ía</div>
      <div class="header-tagline">Tu destino literario</div>
    </div>
    <div class="body">
      {content_html}
    </div>
    <div class="footer">
      <p>© {year} Librería · Todos los derechos reservados</p>
      <p style="margin-top:8px;"><a href="#">Política de privacidad</a> · <a href="#">Términos de uso</a></p>
      <p style="margin-top:12px;color:#5C4A38;">Si no esperabas este correo, puedes ignorarlo sin problema.</p>
    </div>
  </div>
</div>
</body>
</html>"""


# ─── TEMPLATES ESPECÍFICOS ─────────────────────────────────────────────────────

def _template_password_reset(nombre: str, reset_url: str) -> str:
    content = f"""
    <div class="greeting">Hola, {nombre} 👋</div>
    <div class="divider"></div>
    <p class="text">Recibimos una solicitud para restablecer la contraseña de tu cuenta en Librería.</p>
    <p class="text">Haz clic en el botón de abajo para crear una contraseña nueva. Este enlace <strong>expira en 30 minutos</strong>.</p>
    <div class="btn-wrap">
      <a href="{reset_url}" class="btn">🔑 Restablecer contraseña</a>
    </div>
    <div class="highlight-box">
      <div class="label">⏱ Enlace válido por</div>
      <div class="value">30 minutos</div>
    </div>
    <p class="text">Si no solicitaste este cambio, puedes ignorar este correo. Tu contraseña actual seguirá siendo la misma.</p>
    <div class="note">Por seguridad, nunca compartimos tu contraseña ni te la pediremos por correo o teléfono.</div>
    """
    return _base_template(content, preheader="Restablece tu contraseña en Librería — enlace válido por 30 minutos")


def _template_purchase_confirmation(
    nombre: str,
    numero_factura: str,
    items: list,
    subtotal: float,
    impuesto: float,
    total: float,
    fecha: str,
) -> str:
    rows = ""
    for item in items:
        rows += f"""
        <tr>
          <td>{item['nombre']}</td>
          <td style="text-align:center;">{item['cantidad']}</td>
          <td style="text-align:right;">L. {item['precio']:.2f}</td>
          <td style="text-align:right;">L. {item['subtotal']:.2f}</td>
        </tr>"""

    content = f"""
    <div class="greeting">¡Gracias por tu compra, {nombre}! 🎉</div>
    <div class="divider"></div>
    <p class="text">Tu pedido ha sido confirmado y procesado con éxito. Aquí tienes el resumen:</p>
    <div class="highlight-box">
      <div class="label">Número de factura</div>
      <div class="value">{numero_factura}</div>
      <div style="font-size:13px;color:#8B7355;margin-top:4px;">{fecha}</div>
    </div>
    <table class="table">
      <thead>
        <tr>
          <th>Libro</th>
          <th style="text-align:center;">Cant.</th>
          <th style="text-align:right;">Precio</th>
          <th style="text-align:right;">Subtotal</th>
        </tr>
      </thead>
      <tbody>
        {rows}
        <tr>
          <td colspan="3" style="text-align:right;color:#8B7355;font-size:13px;">Subtotal</td>
          <td style="text-align:right;color:#8B7355;">L. {subtotal:.2f}</td>
        </tr>
        <tr>
          <td colspan="3" style="text-align:right;color:#8B7355;font-size:13px;">ISV (15%)</td>
          <td style="text-align:right;color:#8B7355;">L. {impuesto:.2f}</td>
        </tr>
        <tr class="total-row">
          <td colspan="3" style="text-align:right;">Total pagado</td>
          <td style="text-align:right;color:#C9A96E;">L. {total:.2f}</td>
        </tr>
      </tbody>
    </table>
    <p class="text">Los libros digitales (PDF) ya están disponibles en tu biblioteca personal dentro de tu cuenta.</p>
    <div class="btn-wrap">
      <a href="#" class="btn">📚 Ver mis libros</a>
    </div>
    <div class="note">Conserva este correo como comprobante de tu compra. El número de factura es <strong>{numero_factura}</strong>.</div>
    """
    return _base_template(content, preheader=f"Confirmación de compra · Factura {numero_factura}")


def _template_low_stock_alert(libros: list) -> str:
    rows = ""
    for libro in libros:
        urgente = libro.get('urgente', False)
        badge = '<span class="badge badge-warning">⚠ Urgente</span>' if urgente else '<span class="badge" style="background:#FEE2E2;color:#991B1B;">🔴 Crítico</span>'
        rows += f"""
        <tr>
          <td><strong>{libro['nombre']}</strong><br><span style="color:#8B7355;font-size:12px;">{libro['autor']}</span></td>
          <td style="text-align:center;"><strong style="color:#C0392B;">{libro['stock']}</strong></td>
          <td style="text-align:center;">{libro['stock_minimo']}</td>
          <td>{badge}</td>
        </tr>"""

    content = f"""
    <div class="greeting">⚠ Alerta de stock bajo</div>
    <div class="divider"></div>
    <p class="text">El sistema experto ha detectado <strong>{len(libros)} libro(s)</strong> con niveles de inventario críticos que requieren reposición:</p>
    <table class="table">
      <thead>
        <tr>
          <th>Libro</th>
          <th style="text-align:center;">Stock actual</th>
          <th style="text-align:center;">Mínimo</th>
          <th>Estado</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
    <div class="btn-wrap">
      <a href="#" class="btn">📦 Gestionar inventario</a>
    </div>
    <div class="note">Este es un aviso automático generado por el sistema experto de inventario de Librería.</div>
    """
    return _base_template(content, preheader=f"Alerta: {len(libros)} libros necesitan reposición urgente")


def _template_welcome(nombre: str) -> str:
    content = f"""
    <div class="greeting">¡Bienvenido a Librería, {nombre}! 📚</div>
    <div class="divider"></div>
    <p class="text">Nos alegra tenerte con nosotros. Tu cuenta ha sido creada exitosamente y ya puedes explorar nuestra colección de libros.</p>
    <p class="text">Con tu cuenta puedes:</p>
    <div class="highlight-box">
      <p style="margin-bottom:8px;">📖 <strong>Explorar el catálogo</strong> — Miles de títulos en todas las categorías</p>
      <p style="margin-bottom:8px;">⭐ <strong>Recomendaciones personalizadas</strong> — Basadas en tus gustos</p>
      <p style="margin-bottom:8px;">🛒 <strong>Comprar en línea</strong> — Seguro y rápido</p>
      <p>📱 <strong>Tu biblioteca digital</strong> — Lee tus libros cuando quieras</p>
    </div>
    <div class="btn-wrap">
      <a href="#" class="btn">🚀 Explorar catálogo</a>
    </div>
    <div class="note">Si tienes alguna pregunta, nuestro equipo está disponible para ayudarte.</div>
    """
    return _base_template(content, preheader=f"¡Bienvenido {nombre}! Tu cuenta en Librería está lista")


# ─── SEND EMAIL ───────────────────────────────────────────────────────────────

def _send_email(to_email: str, subject: str, html_content: str) -> bool:
    """Envía un email usando SMTP. Retorna True si fue exitoso."""
    smtp_host = getattr(settings, 'SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(getattr(settings, 'SMTP_PORT', 587))
    smtp_user = getattr(settings, 'SMTP_USER', '')
    smtp_pass = getattr(settings, 'SMTP_PASSWORD', '')
    from_name = getattr(settings, 'EMAIL_FROM_NAME', 'Librería')
    from_email = getattr(settings, 'EMAIL_FROM', smtp_user)

    if not smtp_user or not smtp_pass:
        print(f"[EMAIL] SMTP no configurado. Para: {to_email} | Asunto: {subject}")
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{from_name} <{from_email}>"
        msg['To'] = to_email

        plain = "Este correo requiere un cliente de email con soporte HTML."
        msg.attach(MIMEText(plain, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))

        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls(context=context)
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_email, to_email, msg.as_string())

        print(f"[EMAIL] ✅ Enviado a {to_email}")
        return True
    except Exception as e:
        print(f"[EMAIL] ❌ Error enviando a {to_email}: {e}")
        return False


# ─── PUBLIC API ───────────────────────────────────────────────────────────────

def send_password_reset_email(to_email: str, nombre: str, reset_url: str) -> bool:
    html = _template_password_reset(nombre, reset_url)
    return _send_email(to_email, "🔑 Restablece tu contraseña — Librería", html)


def send_purchase_confirmation_email(
    to_email: str,
    nombre: str,
    numero_factura: str,
    items: list,
    subtotal: float,
    impuesto: float,
    total: float,
) -> bool:
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    html = _template_purchase_confirmation(nombre, numero_factura, items, subtotal, impuesto, total, fecha)
    return _send_email(to_email, f"✅ Confirmación de compra · {numero_factura}", html)


def send_low_stock_alert_email(to_email: str, libros: list) -> bool:
    html = _template_low_stock_alert(libros)
    return _send_email(to_email, f"⚠ Alerta de stock bajo — {len(libros)} libros", html)


def send_welcome_email(to_email: str, nombre: str) -> bool:
    html = _template_welcome(nombre)
    return _send_email(to_email, f"¡Bienvenido a Librería, {nombre}! 📚", html)
