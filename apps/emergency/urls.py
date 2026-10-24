from django.urls import path

from . import views

app_name = 'emergency'

urlpatterns = [
    path('', views.sos_dashboard_view, name='dashboard'),
    path('ice/rotate/', views.rotate_ice_token_view, name='rotate_ice_token'),
    path('ice/<uuid:token>/', views.public_ice_view, name='ice'),
]
