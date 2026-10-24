from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path(
        'login/',
        auth_views.LoginView.as_view(template_name='accounts/login.html'),
        name='login',
    ),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', views.account_home_view, name='home'),
    path('profile/', views.profile_detail_view, name='profile_detail'),
    path('profiles/create/', views.profile_create_view, name='profile_create'),
    path(
        'profiles/<int:profile_id>/edit/',
        views.profile_edit_view,
        name='profile_edit',
    ),
    path('profiles/switch/', views.profile_switch_view, name='profile_switch'),
]
