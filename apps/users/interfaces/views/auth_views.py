from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.contrib.messages import get_messages

@never_cache
def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        dni = request.POST.get('dni')
        password = request.POST.get('password')
        
        user = authenticate(request, dni=dni, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('core:dashboard')
        else:
            messages.error(request, 'DNI o contraseña incorrectos.')

    return render(request, 'users/login.html')

@never_cache
def logout_view(request):
    # CORRECCIÓN: Limpiamos cualquier mensaje residual antes de cerrar sesión
    storage = get_messages(request)
    for _ in storage: 
        pass 
        
    logout(request)
    return redirect('users:login')

@login_required(login_url='/auth/login/')
def password_change_view(request):
    if request.user.password_changed:
        return redirect('core:dashboard')

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if new_password and new_password == confirm_password:
            user = request.user
            user.set_password(new_password)
            user.password_changed = True
            user.save()
            
            update_session_auth_hash(request, user) 
            messages.success(request, '¡Contraseña actualizada con éxito!')
            return redirect('core:dashboard')
        else:
            messages.error(request, 'Las contraseñas no coinciden o están vacías.')
            
    return render(request, 'users/password_change.html')