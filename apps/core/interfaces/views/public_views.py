from django.shortcuts import render
from apps.core.infrastructure.repositories.core_repository import DjangoEventRepository
from apps.core.core.use_cases.manage_events import GetPublicEventsUseCase

def home_view(request):
    event_repo = DjangoEventRepository()
    use_case = GetPublicEventsUseCase(event_repo)
    
    eventos = use_case.execute()
    
    return render(request, 'core/home.html', {'eventos': eventos})