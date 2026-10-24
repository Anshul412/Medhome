from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from accounts.utils import get_active_profile

from .models import CheckupReminder, DoseSchedule


@login_required
@require_GET
def dashboard_view(request):
    profile = get_active_profile(request)
    if profile is None:
        messages.info(request, 'Select a patient profile first.')
        return redirect('accounts:profile_switch')

    checkups = CheckupReminder.objects.filter(
        profile=profile,
        is_completed=False,
    ).order_by('due_date', 'pk')
    doses = DoseSchedule.objects.filter(
        profile=profile,
        medication__prescription__condition__profile=profile,
    ).select_related('medication').order_by('scheduled_time', 'pk')
    return render(
        request,
        'reminders/dashboard.html',
        {
            'profile': profile,
            'checkups': checkups,
            'doses': doses,
        },
    )


@login_required
@require_POST
def toggle_dose_view(request, dose_pk):
    profile = get_active_profile(request)
    if profile is None:
        return JsonResponse(
            {'detail': 'Select a patient profile first.'},
            status=400,
        )

    dose = get_object_or_404(
        DoseSchedule.objects.select_related('medication'),
        pk=dose_pk,
        profile=profile,
        medication__prescription__condition__profile=profile,
    )
    dose.is_taken = not dose.is_taken_today
    dose.last_taken_at = timezone.now() if dose.is_taken else None
    dose.save(update_fields=('is_taken', 'last_taken_at'))

    if request.headers.get('Accept') == 'application/json' or (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    ):
        return JsonResponse({
            'id': dose.pk,
            'is_taken': dose.is_taken_today,
            'last_taken_at': dose.last_taken_at.isoformat() if dose.last_taken_at else None,
        })
    messages.success(request, 'Medication checklist updated.')
    return redirect('reminders:dashboard')
