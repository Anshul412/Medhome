from django.urls import path

from . import views

app_name = 'prescriptions'

urlpatterns = [
    path('', views.vault_list, name='vault_list'),
    path('', views.vault_list, name='list'),
    path(
        'conditions/add/',
        views.add_condition,
        name='add_condition',
    ),
    path('upload/', views.prescription_upload_view, name='upload'),
    path(
        'documents/<int:prescription_pk>/',
        views.prescription_document_view,
        name='document',
    ),
    path(
        'conditions/<int:condition_pk>/',
        views.condition_detail_view,
        name='condition_detail',
    ),
]
