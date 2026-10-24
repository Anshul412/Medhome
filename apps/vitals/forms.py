from django import forms

from .models import LifestyleLog, VitalsLog


class VitalsLogForm(forms.ModelForm):
    class Meta:
        model = VitalsLog
        fields = (
            'recorded_at',
            'systolic',
            'diastolic',
            'pulse',
            'spo2',
            'blood_glucose',
            'notes',
        )
        widgets = {
            'recorded_at': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class LifestyleLogForm(forms.ModelForm):
    class Meta:
        model = LifestyleLog
        fields = ('date', 'water_intake_ml', 'calories_kcal')
        widgets = {'date': forms.DateInput(attrs={'type': 'date'})}
