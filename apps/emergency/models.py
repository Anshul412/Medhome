from django.core.validators import MinValueValidator
from django.db import models

from accounts.models import PatientProfile


class EmergencyContact(models.Model):
    profile = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='emergency_contacts',
    )
    name = models.CharField(max_length=200)
    relationship = models.CharField(max_length=64, blank=True)
    phone_number = models.CharField(max_length=32)
    priority = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        help_text='Contact order for emergency calls; 1 is the first contact.',
    )

    class Meta:
        ordering = ('profile', 'priority', 'pk')
        constraints = [
            models.UniqueConstraint(
                fields=('profile', 'priority'),
                name='unique_emergency_contact_priority',
            ),
        ]

    def __str__(self):
        return f'{self.name} ({self.profile.full_name})'
