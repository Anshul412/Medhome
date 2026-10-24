from django.urls import path

from . import views

app_name = 'vitals'

urlpatterns = [
    path('dashboard/', views.log_view, name='dashboard'),
    path('', views.log_view, name='log'),
    path('chart-data/', views.vitals_chart_data, name='chart_data'),
    path('api/chart-data/', views.vitals_chart_data, name='chart_data_api'),
]
