from django import forms

from .models import MedicalCondition, Prescription


class MedicalConditionForm(forms.ModelForm):
    class Meta:
        model = MedicalCondition
        fields = ('name', 'diagnosed_date', 'is_active')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': (
                    'block w-full rounded-lg border-2 border-slate-600 px-4 '
                    'py-3 text-lg text-slate-950'
                ),
                'autocomplete': 'off',
            }),
            'diagnosed_date': forms.DateInput(attrs={
                'class': (
                    'block w-full rounded-lg border-2 border-slate-600 px-4 '
                    'py-3 text-lg text-slate-950'
                ),
                'type': 'date',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 rounded border-2 border-slate-600',
            }),
        }


class PrescriptionUploadForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = (
            'condition',
            'doctor_name',
            'clinic_name',
            'prescription_file',
            'issued_date',
            'notes',
        )
        widgets = {
            'issued_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, profile, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['condition'].queryset = profile.medical_conditions.all()
