from django.shortcuts import render

def home_view(request):
    # La portada es deliberadamente pública y no consulta la agenda interna.
    return render(request, 'core/home.html')
