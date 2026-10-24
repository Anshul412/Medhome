from django.contrib import admin

from .models import CheckupReminder, DoseSchedule


@admin.register(CheckupReminder)
class CheckupReminderAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'profile',
        'doctor_or_lab',
        'due_date',
        'recurrence',
        'is_completed',
    )
    list_filter = ('is_completed', 'recurrence', 'due_date')
    search_fields = ('title', 'doctor_or_lab', 'profile__full_name')
    autocomplete_fields = ('profile',)
    list_select_related = ('profile',)
    date_hierarchy = 'due_date'


@admin.register(DoseSchedule)
class DoseScheduleAdmin(admin.ModelAdmin):
    list_display = (
        'medication',
        'profile',
        'scheduled_time',
        'is_taken',
        'last_taken_at',
    )
    list_filter = ('is_taken', 'scheduled_time')
    search_fields = (
        'medication__medicine_name',
        'profile__full_name',
    )
    autocomplete_fields = ('medication', 'profile')
    list_select_related = ('medication', 'profile')
