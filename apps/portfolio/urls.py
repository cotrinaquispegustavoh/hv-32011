from django.urls import path
from .interfaces.views import portfolio_views

app_name = 'portfolio'

urlpatterns = [
    path('', portfolio_views.portfolio_list_view, name='list'),
    path('subir/', portfolio_views.upload_item_view, name='upload'),
    path('revision/', portfolio_views.portfolio_review_view, name='review_panel'),
    path('observacion/<int:item_id>/', portfolio_views.add_observation_view, name='add_observation'),
]