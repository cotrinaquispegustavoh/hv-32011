"""Protecciones del acceso que no dependen de servicios externos."""

import hashlib
import hmac
import ipaddress
import logging
from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.core.infrastructure.models import AuditLog
from apps.users.infrastructure.models import LoginThrottle, User


logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Acepta X-Forwarded-For únicamente desde un proxy configurado."""

    remote_addr = (request.META.get('REMOTE_ADDR') or '').strip()
    candidate = remote_addr
    if remote_addr in settings.TRUSTED_PROXY_IPS:
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if forwarded:
            candidate = forwarded.split(',', 1)[0].strip()
    try:
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        return None


def _throttle_key(scope, value):
    value = str(value or '').strip().casefold()
    payload = f'{scope}:{value}'.encode('utf-8')
    return hmac.new(
        settings.SECRET_KEY.encode('utf-8'),
        payload,
        hashlib.sha256,
    ).hexdigest()


def _attempt_limit(scope):
    if scope == 'ACCOUNT':
        return max(settings.LOGIN_RATE_ACCOUNT_ATTEMPTS, 1)
    return max(settings.LOGIN_RATE_IP_ATTEMPTS, 1)


def login_is_allowed(identifier, client_ip):
    now = timezone.now()
    keys = [_throttle_key('ACCOUNT', identifier)]
    if client_ip:
        keys.append(_throttle_key('IP', client_ip))
    return not LoginThrottle.objects.filter(
        key__in=keys,
        blocked_until__gt=now,
    ).exists()


def _register_scope_failure(scope, value, now):
    if not value:
        return False
    key = _throttle_key(scope, value)
    window = timedelta(seconds=max(settings.LOGIN_RATE_WINDOW_SECONDS, 1))
    threshold = _attempt_limit(scope)
    base_lock = max(settings.LOGIN_RATE_LOCK_SECONDS, 1)
    max_lock = max(settings.LOGIN_RATE_MAX_LOCK_SECONDS, base_lock)

    with transaction.atomic():
        try:
            throttle = LoginThrottle.objects.select_for_update().get(key=key)
        except LoginThrottle.DoesNotExist:
            try:
                with transaction.atomic():
                    throttle = LoginThrottle.objects.create(
                        key=key,
                        scope=scope,
                        window_started_at=now,
                    )
            except IntegrityError:
                # Otra petición creó el contador al mismo tiempo.
                throttle = LoginThrottle.objects.select_for_update().get(key=key)
        if throttle.window_started_at + window <= now:
            throttle.failures = 0
            throttle.window_started_at = now
            throttle.blocked_until = None

        was_blocked = bool(throttle.blocked_until and throttle.blocked_until > now)
        throttle.failures += 1
        if throttle.failures >= threshold:
            exponent = min(throttle.failures - threshold, 4)
            lock_seconds = min(base_lock * (2 ** exponent), max_lock)
            throttle.blocked_until = now + timedelta(seconds=lock_seconds)
        throttle.save()
        return not was_blocked and bool(throttle.blocked_until and throttle.blocked_until > now)


def register_login_failure(identifier, client_ip):
    """Incrementa ambos límites y registra solamente el inicio de un bloqueo."""

    now = timezone.now()
    account_blocked = _register_scope_failure('ACCOUNT', identifier, now)
    ip_blocked = _register_scope_failure('IP', client_ip, now)
    if not (account_blocked or ip_blocked):
        return

    user = User.objects.filter(dni=str(identifier or '').strip()).first()
    AuditLog.objects.create(
        user=user,
        action='LOGIN_BLOCKED',
        model_name='User',
        object_id=_throttle_key('ACCOUNT', identifier)[:16],
        changes={
            'info': 'Acceso bloqueado temporalmente por intentos fallidos repetidos.',
        },
        ip_address=client_ip,
    )
    logger.warning(
        'Bloqueo temporal de acceso activado (cuenta=%s, ip=%s).',
        _throttle_key('ACCOUNT', identifier)[:12],
        client_ip or 'no-disponible',
    )


def clear_successful_account_throttle(identifier):
    """Un acceso válido limpia errores de la cuenta, no el contador global de IP."""

    LoginThrottle.objects.filter(key=_throttle_key('ACCOUNT', identifier)).delete()
