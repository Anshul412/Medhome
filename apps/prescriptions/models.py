import uuid

from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models

from accounts.models import PatientProfile


def prescription_upload_path(instance, filename):
    extension = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return f'prescriptions/{uuid.uuid4().hex}.{extension}' if extension else (
        f'prescriptions/{uuid.uuid4().hex}'
    )


class MedicalCondition(models.Model):
    profile = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='medical_conditions',
    )
    name = models.CharField(max_length=200)
    diagnosed_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('name', 'pk')
        indexes = [
            models.Index(fields=('profile', 'is_active'), name='condition_profile_active_idx'),
        ]

    def __str__(self):
        return f'{self.name} ({self.profile.full_name})'


class Prescription(models.Model):
    condition = models.ForeignKey(
        MedicalCondition,
        on_delete=models.CASCADE,
        related_name='prescriptions',
    )
    doctor_name = models.CharField(max_length=200, blank=True)
    clinic_name = models.CharField(max_length=200, blank=True)
    prescription_file = models.FileField(
        upload_to=prescription_upload_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=('pdf', 'jpg', 'jpeg', 'png'),
            ),
        ],
        blank=True,
    )
    issued_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ('-issued_date', '-pk')

    def __str__(self):
        date = self.issued_date.isoformat() if self.issued_date else 'undated'
        return f'{self.condition.name} prescription - {date}'


class MedicationItem(models.Model):
    class MealRelation(models.TextChoices):
        BEFORE = 'before', 'Before meals'
        WITH = 'with', 'With meals'
        AFTER = 'after', 'After meals'
        ANY = 'any', 'No meal preference'

    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name='medications',
    )
    medicine_name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=120)
    frequency = models.CharField(max_length=120)
    relation_to_meals = models.CharField(
        max_length=12,
        choices=MealRelation.choices,
        blank=True,
    )
    duration_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
    )

    class Meta:
        ordering = ('medicine_name', 'pk')

    def __str__(self):
        return f'{self.medicine_name} - {self.dosage}'
