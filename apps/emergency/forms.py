from django import forms
from django.core.validators import RegexValidator

from .models import EmergencyContact


class EmergencyContactForm(forms.ModelForm):
    phone_number = forms.CharField(
        max_length=32,
        validators=[
            RegexValidator(
                regex=r'^\+?[0-9][0-9 ()-]{5,30}$',
                message='Enter a valid phone number.',
            ),
        ],
    )

    class Meta:
        model = EmergencyContact
        fields = ('name', 'relationship', 'phone_number', 'priority')
