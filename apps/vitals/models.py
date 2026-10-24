from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from accounts.models import PatientProfile


class VitalsLog(models.Model):
    profile = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='vitals_logs',
    )
    recorded_at = models.DateTimeField(default=timezone.now, db_index=True)
    systolic = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
    )
    diastolic = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
    )
    pulse = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
    )
    spo2 = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    blood_glucose = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text='Enter the value in the unit used by your care team.',
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ('-recorded_at', '-pk')
        indexes = [
            models.Index(
                fields=('profile', '-recorded_at'),
                name='vitals_profile_recorded_idx',
            ),
        ]

    def __str__(self):
        return f'{self.profile.full_name} - {self.recorded_at:%Y-%m-%d %H:%M}'


class LifestyleLog(models.Model):
    profile = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='lifestyle_logs',
    )
    date = models.DateField(default=timezone.localdate)
    water_intake_ml = models.PositiveIntegerField(default=0)
    calories_kcal = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('-date', '-pk')
        constraints = [
            models.UniqueConstraint(
                fields=('profile', 'date'),
                name='unique_lifestyle_log_per_profile_day',
            ),
        ]

    def __str__(self):
        return f'{self.profile.full_name} - {self.date}'
