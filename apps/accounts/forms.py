from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import PatientProfile


class SignUpForm(UserCreationForm):
    email = forms.EmailField()
    phone_number = forms.CharField(max_length=32, required=False)

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ('username', 'first_name', 'last_name', 'email', 'phone_number')


class PatientProfileForm(forms.ModelForm):
    class Meta:
        model = PatientProfile
        fields = (
            'full_name',
            'relationship',
            'dob',
            'blood_group',
            'chronic_conditions',
            'emergency_notes',
        )
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date'}),
            'chronic_conditions': forms.Textarea(attrs={'rows': 3}),
            'emergency_notes': forms.Textarea(attrs={'rows': 3}),
        }


class ProfileSwitchForm(forms.Form):
    profile = forms.ModelChoiceField(
        queryset=PatientProfile.objects.none(),
        empty_label=None,
    )

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['profile'].queryset = PatientProfile.objects.filter(
            user=user,
        ).order_by('full_name', 'pk')
