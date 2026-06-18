from django.urls import path
from .interfaces.views import catalog_views, loan_views, dispatch_views

app_name = 'warehouse'

urlpatterns = [
    path('catalogo/', catalog_views.catalog_view, name='catalog'),
    path('solicitar/<int:material_id>/', loan_views.request_material_view, name='request_material'),
    
    path('despacho/', dispatch_views.dispatch_panel_view, name='dispatch_panel'),
    path('despacho/actualizar/<int:loan_id>/', dispatch_views.update_loan_status_view, name='update_loan_status'),
]