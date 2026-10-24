from django.urls import path

from . import views

app_name = 'reminders'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('doses/<int:dose_pk>/toggle/', views.toggle_dose_view, name='toggle_dose'),
]
