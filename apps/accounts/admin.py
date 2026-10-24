from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, PatientProfile


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'is_caregiver', 'is_staff')
    list_filter = (*UserAdmin.list_filter, 'is_caregiver')
    search_fields = (*UserAdmin.search_fields, 'phone_number')
    fieldsets = (
        *UserAdmin.fieldsets,
        ('MedHome', {'fields': ('phone_number', 'is_caregiver')}),
    )
    add_fieldsets = (
        *UserAdmin.add_fieldsets,
        ('MedHome', {'fields': ('phone_number', 'is_caregiver')}),
    )


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'relationship', 'dob', 'blood_group')
    list_filter = ('blood_group', 'relationship')
    search_fields = ('full_name', 'user__username', 'user__email', 'chronic_conditions')
    autocomplete_fields = ('user',)
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('user',)
