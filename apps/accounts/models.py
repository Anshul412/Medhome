import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=32, blank=True)
    is_caregiver = models.BooleanField(default=False)

    def __str__(self):
        return self.get_full_name() or self.username


class PatientProfile(models.Model):
    ice_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    class BloodGroup(models.TextChoices):
        A_POSITIVE = 'A+', 'A+'
        A_NEGATIVE = 'A-', 'A-'
        B_POSITIVE = 'B+', 'B+'
        B_NEGATIVE = 'B-', 'B-'
        AB_POSITIVE = 'AB+', 'AB+'
        AB_NEGATIVE = 'AB-', 'AB-'
        O_POSITIVE = 'O+', 'O+'
        O_NEGATIVE = 'O-', 'O-'
        UNKNOWN = 'unknown', 'Unknown'

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='patient_profiles',
    )
    full_name = models.CharField(max_length=200)
    relationship = models.CharField(max_length=64, blank=True)
    dob = models.DateField(null=True, blank=True)
    blood_group = models.CharField(
        max_length=7,
        choices=BloodGroup.choices,
        blank=True,
    )
    chronic_conditions = models.TextField(blank=True)
    emergency_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('full_name', 'pk')
        indexes = [
            models.Index(fields=('user', 'full_name'), name='profile_user_name_idx'),
        ]

    def __str__(self):
        return self.full_name
