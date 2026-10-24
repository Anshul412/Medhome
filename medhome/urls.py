"""
URL configuration for medhome project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from accounts.views import landing_view

admin.site.site_header = 'MedHome Database'
admin.site.site_title = 'MedHome Database'
admin.site.index_title = 'Healthcare records'

urlpatterns = [
    path('', landing_view, name='home'),
    path('admin/', admin.site.urls),
    path('admin-panel/', include('admin_panel.urls')),
    path('accounts/', include('accounts.urls')),
    path('vitals/', include('vitals.urls')),
    path('prescriptions/', include('prescriptions.urls')),
    path('reminders/', include('reminders.urls')),
    path('emergency/', include('emergency.urls')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
