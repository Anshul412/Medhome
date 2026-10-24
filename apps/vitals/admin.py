from django.contrib import admin

from .models import LifestyleLog, VitalsLog


@admin.register(VitalsLog)
class VitalsLogAdmin(admin.ModelAdmin):
    list_display = (
        'profile',
        'recorded_at',
        'systolic',
        'diastolic',
        'pulse',
        'spo2',
        'blood_glucose',
    )
    list_filter = ('recorded_at',)
    search_fields = ('profile__full_name', 'notes')
    date_hierarchy = 'recorded_at'
    autocomplete_fields = ('profile',)
    list_select_related = ('profile',)


@admin.register(LifestyleLog)
class LifestyleLogAdmin(admin.ModelAdmin):
    list_display = ('profile', 'date', 'water_intake_ml', 'calories_kcal')
    list_filter = ('date',)
    search_fields = ('profile__full_name',)
    date_hierarchy = 'date'
    autocomplete_fields = ('profile',)
    list_select_related = ('profile',)
