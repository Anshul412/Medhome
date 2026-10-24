from django.contrib import admin

from .models import EmergencyContact


@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'profile', 'relationship', 'phone_number', 'priority')
    list_filter = ('relationship',)
    search_fields = ('name', 'phone_number', 'profile__full_name')
    autocomplete_fields = ('profile',)
    list_select_related = ('profile',)
    ordering = ('profile', 'priority')
