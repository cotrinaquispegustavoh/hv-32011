from django.urls import path
from .interfaces.views import portfolio_views

app_name = 'portfolio'

urlpatterns = [
    path('', portfolio_views.portfolio_list_view, name='list'),
    path('subir/', portfolio_views.upload_item_view, name='upload'),
]