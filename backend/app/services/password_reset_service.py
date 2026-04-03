"""
Servicio de recuperación de contraseña.
Usa tokens seguros almacenados en memoria (válido para SQLite/desarrollo).
Para producción, considera almacenarlos en Redis o en la DB.
"""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.core.security import get_password_hash
from app.core.config import get_settings
from app.services.email_service import send_password_reset_email

settings = get_settings()

# Store en memoria: token -> {user_id, expires_at}
_reset_tokens: dict = {}


def _cleanup_expired():
    """Limpia tokens expirados."""
    now = datetime.now(timezone.utc)
    expired = [t for t, data in _reset_tokens.items() if data['expires_at'] < now]
    for t in expired:
        del _reset_tokens[t]


def request_password_reset(db: Session, email: str) -> bool:
    """
    Genera token de reset y envía email.
    Siempre retorna True para no revelar si el email existe.
    """
    _cleanup_expired()

    user = db.query(User).filter(User.email == email, User.activo == True).first()
    if not user:
        return True  # No revelar que el email no existe

    # Revocar token anterior si existe
    old = [t for t, d in _reset_tokens.items() if d['user_id'] == user.id]
    for t in old:
        del _reset_tokens[t]

    # Generar token seguro
    token = secrets.token_urlsafe(48)
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES)

    _reset_tokens[token] = {
        'user_id': user.id,
        'email': user.email,
        'expires_at': expires,
    }

    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    send_password_reset_email(user.email, user.nombre, reset_url)

    return True


def confirm_password_reset(db: Session, token: str, new_password: str) -> bool:
    """Verifica el token y actualiza la contraseña."""
    _cleanup_expired()

    data = _reset_tokens.get(token)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El enlace es inválido o ha expirado. Solicita uno nuevo."
        )

    if datetime.now(timezone.utc) > data['expires_at']:
        del _reset_tokens[token]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El enlace ha expirado. Solicita uno nuevo."
        )

    user = db.query(User).filter(User.id == data['user_id'], User.activo == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado."
        )

    user.password_hash = get_password_hash(new_password)
    db.commit()

    # Invalidar token usado
    del _reset_tokens[token]

    return True


def validate_reset_token(token: str) -> Optional[str]:
    """Valida un token y retorna el email asociado, o None si inválido."""
    _cleanup_expired()
    data = _reset_tokens.get(token)
    if not data:
        return None
    if datetime.now(timezone.utc) > data['expires_at']:
        return None
    return data.get('email')
