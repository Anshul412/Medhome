from django.contrib import admin

from .models import MedicalCondition, MedicationItem, Prescription


@admin.register(MedicalCondition)
class MedicalConditionAdmin(admin.ModelAdmin):
    list_display = ('name', 'profile', 'diagnosed_date', 'is_active')
    list_filter = ('is_active', 'diagnosed_date')
    search_fields = ('name', 'profile__full_name')
    autocomplete_fields = ('profile',)
    list_select_related = ('profile',)


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('condition', 'doctor_name', 'clinic_name', 'issued_date')
    list_filter = ('issued_date',)
    search_fields = (
        'condition__name',
        'condition__profile__full_name',
        'doctor_name',
        'clinic_name',
    )
    autocomplete_fields = ('condition',)
    list_select_related = ('condition', 'condition__profile')
    date_hierarchy = 'issued_date'


@admin.register(MedicationItem)
class MedicationItemAdmin(admin.ModelAdmin):
    list_display = (
        'medicine_name',
        'prescription',
        'dosage',
        'frequency',
        'relation_to_meals',
        'duration_days',
    )
    list_filter = ('relation_to_meals',)
    search_fields = (
        'medicine_name',
        'prescription__condition__name',
        'prescription__condition__profile__full_name',
    )
    autocomplete_fields = ('prescription',)
    list_select_related = ('prescription', 'prescription__condition')
