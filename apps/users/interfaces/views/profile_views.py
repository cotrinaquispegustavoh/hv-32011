from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.users.interfaces.forms import AccountPasswordChangeForm, UserProfileForm


@login_required(login_url='/auth/login/')
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tu información personal fue actualizada correctamente.')
            return redirect('users:profile')
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'users/profile.html', {'form': form})


@login_required(login_url='/auth/login/')
def security_view(request):
    if request.method == 'POST':
        form = AccountPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Tu contraseña fue actualizada correctamente.')
            return redirect('users:security')
    else:
        form = AccountPasswordChangeForm(request.user)

    return render(request, 'users/security.html', {
        'form': form,
        'session_expires_at': request.session.get_expiry_date(),
    })
