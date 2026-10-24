from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from accounts.models import PatientProfile
from prescriptions.models import MedicationItem


class CheckupReminder(models.Model):
    class Recurrence(models.TextChoices):
        ONCE = 'once', 'Does not repeat'
        DAILY = 'daily', 'Daily'
        WEEKLY = 'weekly', 'Weekly'
        MONTHLY = 'monthly', 'Monthly'
        YEARLY = 'yearly', 'Yearly'

    profile = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='checkup_reminders',
    )
    title = models.CharField(max_length=200)
    doctor_or_lab = models.CharField(max_length=200, blank=True)
    due_date = models.DateTimeField()
    recurrence = models.CharField(
        max_length=12,
        choices=Recurrence.choices,
        default=Recurrence.ONCE,
    )
    is_completed = models.BooleanField(default=False)

    class Meta:
        ordering = ('due_date', 'pk')
        indexes = [
            models.Index(
                fields=('profile', 'is_completed', 'due_date'),
                name='checkup_profile_status_due_idx',
            ),
        ]

    def __str__(self):
        return f'{self.title} - {self.due_date:%Y-%m-%d}'


class DoseSchedule(models.Model):
    medication = models.ForeignKey(
        MedicationItem,
        on_delete=models.CASCADE,
        related_name='dose_schedules',
    )
    profile = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='dose_schedules',
    )
    scheduled_time = models.TimeField()
    is_taken = models.BooleanField(default=False)
    last_taken_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('scheduled_time', 'pk')
        indexes = [
            models.Index(fields=('profile', 'scheduled_time'), name='dose_profile_time_idx'),
        ]

    def clean(self):
        super().clean()
        if (
            self.medication_id
            and self.profile_id
            and self.medication.prescription.condition.profile_id != self.profile_id
        ):
            raise ValidationError({
                'profile': 'Select the patient profile linked to this medication.',
            })

    def __str__(self):
        return f'{self.medication.medicine_name} at {self.scheduled_time:%H:%M}'

    @property
    def is_taken_today(self):
        return bool(
            self.is_taken
            and self.last_taken_at
            and timezone.localtime(self.last_taken_at).date() == timezone.localdate()
        )
