from django import forms

from accounts.models import PatientProfile
from prescriptions.models import MedicationItem

from .models import CheckupReminder, DoseSchedule


class CheckupReminderForm(forms.ModelForm):
    class Meta:
        model = CheckupReminder
        fields = ('title', 'doctor_or_lab', 'due_date', 'recurrence')
        widgets = {
            'due_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
        }


class DoseScheduleForm(forms.ModelForm):
    class Meta:
        model = DoseSchedule
        fields = ('medication', 'scheduled_time')
        widgets = {'scheduled_time': forms.TimeInput(attrs={'type': 'time'})}

    def __init__(self, *args, profile: PatientProfile, **kwargs):
        super().__init__(*args, **kwargs)
        self.profile = profile
        self.fields['medication'].queryset = MedicationItem.objects.filter(
            prescription__condition__profile=profile,
        )

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.profile = self.profile
        if commit:
            instance.full_clean()
            instance.save()
        return instance
