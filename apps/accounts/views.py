from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import PatientProfileForm, ProfileSwitchForm, SignUpForm
from .models import PatientProfile
from .utils import get_active_profile


def landing_view(request):
    if request.user.is_authenticated:
        return redirect('vitals:dashboard')
    return render(request, 'home.html')


@require_http_methods(['GET', 'POST'])
def signup_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:profile_create')

    form_data = request.POST if request.method == 'POST' else None
    form = SignUpForm(form_data)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('accounts:profile_create')
    if request.method == 'POST':
        messages.error(request, 'Account was not created. Check the form errors below.')

    return render(request, 'accounts/register.html', {'form': form})


@login_required
@require_http_methods(['GET', 'POST'])
def profile_create_view(request):
    form_data = request.POST if request.method == 'POST' else None
    form = PatientProfileForm(form_data)
    if request.method == 'POST' and form.is_valid():
        profile = form.save(commit=False)
        profile.user = request.user
        profile.save()
        request.session['active_profile_id'] = profile.pk
        messages.success(request, 'Patient profile created.')
        return redirect('accounts:profile_switch')
    if request.method == 'POST':
        messages.error(request, 'Patient profile was not saved. Check the form errors below.')

    return render(request, 'accounts/profile_form.html', {'form': form})


@login_required
def profile_detail_view(request):
    profiles = PatientProfile.objects.filter(user=request.user)
    if not profiles.exists():
        messages.info(request, 'Create a patient profile to continue.')
        return redirect('accounts:profile_create')

    active_profile = get_active_profile(request)
    if active_profile is None:
        return redirect('accounts:profile_switch')

    return render(
        request,
        'accounts/profile_detail.html',
        {'profile': active_profile},
    )


@login_required
@require_http_methods(['GET', 'POST'])
def profile_edit_view(request, profile_id):
    profile = get_object_or_404(
        PatientProfile,
        pk=profile_id,
        user=request.user,
    )
    form = PatientProfileForm(
        request.POST or None,
        instance=profile,
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Patient profile updated.')
        return redirect('accounts:profile_detail')
    if request.method == 'POST':
        messages.error(request, 'Patient profile was not updated. Check the form errors below.')

    return render(
        request,
        'accounts/profile_form.html',
        {'form': form, 'profile': profile},
    )


@login_required
@require_http_methods(['GET', 'POST'])
def profile_switch_view(request):
    profiles = PatientProfile.objects.filter(user=request.user)
    if not profiles.exists():
        messages.info(request, 'Create a patient profile to continue.')
        return redirect('accounts:profile_create')

    active_profile = get_active_profile(request)
    initial = {'profile': active_profile} if active_profile else None
    form_data = request.POST if request.method == 'POST' else None
    form = ProfileSwitchForm(
        form_data,
        user=request.user,
        initial=initial,
    )
    if request.method == 'POST' and form.is_valid():
        profile = form.cleaned_data['profile']
        request.session['active_profile_id'] = profile.pk
        messages.success(request, f'Now viewing {profile.full_name}.')
        return redirect('vitals:log')
    if request.method == 'POST':
        messages.error(request, 'Profile was not switched. Select one of your profiles.')

    return render(
        request,
        'accounts/profile_switch.html',
        {'form': form, 'active_profile': active_profile},
    )


@login_required
def account_home_view(request):
    return redirect('accounts:profile_switch')
