import logging
import secrets
import string

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.contrib.messages import get_messages
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from apps.users.security import (
    clear_successful_account_throttle,
    get_client_ip,
    invalidate_user_sessions,
    login_is_allowed,
    password_reset_is_allowed,
    register_login_failure,
    register_password_reset_request,
)
from apps.core.infrastructure.models import AuditLog
from apps.users.infrastructure.models import User
from apps.users.interfaces.forms import (
    AdministrativePasswordResetForm,
    PasswordRecoveryRequestForm,
    PasswordRecoverySetForm,
)


logger = logging.getLogger(__name__)

@never_cache
def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        dni = (request.POST.get('dni') or '').strip()
        password = request.POST.get('password')
        client_ip = get_client_ip(request)

        if not login_is_allowed(dni, client_ip):
            messages.error(
                request,
                'Demasiados intentos de acceso. Espera unos minutos e inténtalo nuevamente.',
            )
            return render(request, 'users/login.html', status=429)
        
        user = authenticate(request, dni=dni, password=password)
        
        if user is not None:
            clear_successful_account_throttle(dni)
            login(request, user)
            return redirect('core:dashboard')
        else:
            register_login_failure(dni, client_ip)
            messages.error(request, 'DNI o contraseña incorrectos.')

    return render(request, 'users/login.html')

@never_cache
def logout_view(request):
    # CORRECCIÓN: Limpiamos cualquier mensaje residual antes de cerrar sesión
    storage = get_messages(request)
    for _ in storage: 
        pass 
        
    logout(request)
    return redirect('core:home')

@login_required(login_url='/auth/login/')
def password_change_view(request):
    if request.user.password_changed:
        return redirect('core:dashboard')

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if new_password and new_password == confirm_password:
            user = request.user
            try:
                validate_password(new_password, user=user)
            except ValidationError as exc:
                for error in exc.messages:
                    messages.error(request, error)
                return render(request, 'users/password_change.html')

            user.set_password(new_password)
            user.password_changed = True
            user.save(update_fields=['password', 'password_changed'])
            
            update_session_auth_hash(request, user) 
            messages.success(request, '¡Contraseña actualizada con éxito!')
            return redirect('core:dashboard')
        else:
            messages.error(request, 'Las contraseñas no coinciden o están vacías.')
            
    return render(request, 'users/password_change.html')


@never_cache
def password_reset_request_view(request):
    """Solicita un enlace sin revelar si la identidad está registrada."""

    submitted = False
    form = PasswordRecoveryRequestForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        dni = form.cleaned_data['dni']
        email = form.cleaned_data['email']
        client_ip = get_client_ip(request)
        allowed = password_reset_is_allowed(dni, client_ip)
        if allowed:
            register_password_reset_request(dni, client_ip)
            user = User.objects.filter(
                dni=dni,
                email__iexact=email,
                is_active=True,
            ).exclude(email='').first()
            if user:
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                reset_url = request.build_absolute_uri(
                    reverse('users:password_reset_confirm', args=[uid, token])
                )
                body = render_to_string('users/emails/password_reset.txt', {
                    'user': user,
                    'reset_url': reset_url,
                    'timeout_minutes': max(settings.PASSWORD_RESET_TIMEOUT // 60, 1),
                })
                try:
                    send_mail(
                        'Restablece tu contraseña de Intranet HV',
                        body,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=False,
                    )
                except Exception:
                    logger.exception(
                        'No se pudo enviar el correo de recuperación para el usuario %s.',
                        user.pk,
                    )
                else:
                    AuditLog.objects.create(
                        user=user,
                        action='RESET_REQUEST',
                        model_name='User',
                        object_id=str(user.pk),
                        changes={'info': 'Se envió un enlace temporal de recuperación.'},
                        ip_address=client_ip,
                    )
        submitted = True
        form = PasswordRecoveryRequestForm()

    return render(request, 'users/password_reset_request.html', {
        'form': form,
        'submitted': submitted,
    })


def _password_reset_user(uidb64, token):
    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=user_id, is_active=True)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None
    return user if default_token_generator.check_token(user, token) else None


@never_cache
def password_reset_confirm_view(request, uidb64, token):
    user = _password_reset_user(uidb64, token)
    if user is None:
        return render(request, 'users/password_reset_confirm.html', {
            'validlink': False,
        })

    form = PasswordRecoverySetForm(user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.password_changed = True
        user.save(update_fields=['password', 'password_changed'])
        invalidate_user_sessions(user)
        AuditLog.objects.create(
            user=user,
            action='PASSWORD_RESET',
            model_name='User',
            object_id=str(user.pk),
            changes={'info': 'La cuenta restableció su contraseña mediante un enlace temporal.'},
            ip_address=get_client_ip(request),
        )
        messages.success(
            request,
            'Contraseña restablecida. Ya puedes iniciar sesión.',
            extra_tags='auth-success',
        )
        return redirect('users:login')

    return render(request, 'users/password_reset_confirm.html', {
        'form': form,
        'validlink': True,
    })


def _temporary_password(user):
    alphabet = string.ascii_letters + string.digits
    for _ in range(20):
        random_part = ''.join(secrets.choice(alphabet) for _ in range(10))
        candidate = f'Hv!{random_part}7a'
        try:
            validate_password(candidate, user=user)
        except ValidationError:
            continue
        return candidate
    raise RuntimeError('No se pudo generar una contraseña temporal segura.')


@login_required(login_url='/auth/login/')
@never_cache
def administrative_password_reset_view(request):
    if request.user.role not in ['DIRECTOR', 'SUPERUSER'] and not request.user.is_superuser:
        return HttpResponseForbidden('No tienes permiso para restablecer contraseñas.')

    initial_dni = (request.GET.get('dni') or '').strip()
    form = AdministrativePasswordResetForm(
        request.POST or None,
        initial={'dni': initial_dni},
    )
    temporary_password = None
    target_user = None

    if request.method == 'POST' and form.is_valid():
        target_user = User.objects.filter(dni=form.cleaned_data['dni']).first()
        if target_user is None:
            form.add_error('dni', 'No existe una cuenta con este DNI.')
        elif target_user.pk == request.user.pk:
            form.add_error('dni', 'Para tu propia cuenta utiliza la sección Seguridad.')
        elif (
            target_user.role in ['DIRECTOR', 'SUPERUSER']
            and not request.user.is_superuser
        ):
            form.add_error('dni', 'Solo un superusuario puede restablecer una cuenta directiva o técnica.')
        else:
            temporary_password = _temporary_password(target_user)
            target_user.set_password(temporary_password)
            target_user.password_changed = False
            target_user.save(update_fields=['password', 'password_changed'])
            invalidate_user_sessions(target_user)
            AuditLog.objects.create(
                user=request.user,
                action='ADMIN_RESET',
                model_name='User',
                object_id=str(target_user.pk),
                changes={
                    'info': 'Se generó una contraseña temporal para la cuenta.',
                    'target_role': target_user.role,
                },
                ip_address=get_client_ip(request),
            )

    return render(request, 'users/admin_password_reset.html', {
        'form': form,
        'temporary_password': temporary_password,
        'target_user': target_user,
    })
