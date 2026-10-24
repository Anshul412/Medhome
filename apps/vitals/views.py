from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods

from accounts.utils import get_active_profile

from .forms import LifestyleLogForm, VitalsLogForm
from .models import LifestyleLog, VitalsLog


def _summary_stat(value, unit, *, warning=False, danger=False, empty='Not recorded'):
    if value is None:
        return {'value': empty, 'tone': 'neutral'}
    tone = 'danger' if danger else 'warning' if warning else 'normal'
    return {'value': f'{value} {unit}'.strip(), 'tone': tone}


@login_required
@require_http_methods(['GET', 'POST'])
def log_view(request):
    profile = get_active_profile(request)
    if profile is None:
        messages.info(request, 'Select a patient profile first.')
        return redirect('accounts:profile_switch')

    form_data = request.POST if request.method == 'POST' else None
    vitals_form = VitalsLogForm(form_data, prefix='vitals')
    lifestyle_form = LifestyleLogForm(form_data, prefix='lifestyle')

    if request.method == 'POST':
        form_name = request.POST.get('form_name')
        if form_name == 'vitals' and vitals_form.is_valid():
            entry = vitals_form.save(commit=False)
            entry.profile = profile
            entry.save()
            messages.success(request, 'Vitals saved.')
            return redirect('vitals:log')
        if form_name == 'vitals':
            messages.error(request, 'Vitals were not saved. Check the form errors below.')
        if form_name == 'lifestyle' and lifestyle_form.is_valid():
            entry = lifestyle_form.save(commit=False)
            LifestyleLog.objects.update_or_create(
                profile=profile,
                date=entry.date,
                defaults={
                    'water_intake_ml': entry.water_intake_ml,
                    'calories_kcal': entry.calories_kcal,
                },
            )
            messages.success(request, 'Daily lifestyle log saved.')
            return redirect('vitals:log')
        if form_name == 'lifestyle':
            messages.error(request, 'Lifestyle log was not saved. Check the form errors below.')
        if form_name not in ('vitals', 'lifestyle'):
            messages.error(request, 'The submitted form could not be identified; nothing was saved.')

    latest = VitalsLog.objects.filter(profile=profile).first()
    spo2 = latest.spo2 if latest else None
    systolic = latest.systolic if latest else None
    diastolic = latest.diastolic if latest else None
    pulse = latest.pulse if latest else None
    glucose = latest.blood_glucose if latest else None
    spo2_display = (
        f'{spo2:f}'.rstrip('0').rstrip('.') if spo2 is not None else None
    )
    systolic_warning = systolic is not None and systolic >= 140
    systolic_danger = systolic is not None and systolic < 90
    diastolic_warning = diastolic is not None and diastolic >= 90
    diastolic_danger = diastolic is not None and diastolic < 60

    return render(
        request,
        'vitals/dashboard.html',
        {
            'profile': profile,
            'vitals_form': vitals_form,
            'lifestyle_form': lifestyle_form,
            'latest': latest,
            'bp_stat': _summary_stat(
                f'{systolic}/{diastolic}' if systolic is not None and diastolic is not None else None,
                'mmHg',
                warning=systolic_warning or diastolic_warning,
                danger=systolic_danger or diastolic_danger,
            ),
            'spo2_stat': _summary_stat(
                spo2_display,
                '%',
                warning=spo2 is not None and spo2 >= 94 and spo2 < 96,
                danger=spo2 is not None and spo2 < 94,
            ),
            'pulse_stat': _summary_stat(pulse, 'bpm'),
            'glucose_stat': _summary_stat(glucose, ''),
            'has_pulse': pulse is not None,
            'has_glucose': glucose is not None,
        },
    )


@login_required
@require_GET
def vitals_chart_data(request):
    profile = get_active_profile(request)
    if profile is None:
        return JsonResponse(
            {'detail': 'Select a patient profile first.'},
            status=400,
        )

    end_date = timezone.localdate()
    start_date = end_date - timedelta(days=29)
    logs = VitalsLog.objects.filter(
        profile=profile,
        recorded_at__date__gte=start_date,
        recorded_at__date__lte=end_date,
    ).order_by('recorded_at', 'pk')
    values = {
        'dates': [],
        'systolic': [],
        'diastolic': [],
        'spo2': [],
        'blood_glucose': [],
    }
    for log in logs:
        values['dates'].append(timezone.localtime(log.recorded_at).date().isoformat())
        values['systolic'].append(log.systolic)
        values['diastolic'].append(log.diastolic)
        values['spo2'].append(float(log.spo2) if log.spo2 is not None else None)
        values['blood_glucose'].append(
            float(log.blood_glucose) if log.blood_glucose is not None else None
        )
    return JsonResponse(values)
