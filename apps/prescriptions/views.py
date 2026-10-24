from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from accounts.utils import get_active_profile

from .forms import MedicalConditionForm, PrescriptionUploadForm
from .models import MedicalCondition, Prescription


@login_required
@require_GET
def vault_list(request):
    profile = get_active_profile(request)
    if profile is None:
        messages.info(request, 'Select a patient profile first.')
        return redirect('accounts:profile_switch')

    conditions = (
        MedicalCondition.objects.filter(profile=profile)
        .prefetch_related('prescriptions__medications')
        .order_by('-is_active', 'name', 'pk')
    )
    return render(
        request,
        'prescriptions/vault.html',
        {'profile': profile, 'conditions': conditions},
    )


@login_required
@require_http_methods(['GET', 'POST'])
def add_condition(request):
    profile = get_active_profile(request)
    if profile is None:
        messages.info(request, 'Select a patient profile first.')
        return redirect('accounts:profile_switch')

    form = MedicalConditionForm(
        request.POST if request.method == 'POST' else None,
    )
    if request.method == 'POST':
        if form.is_valid():
            condition = form.save(commit=False)
            condition.profile = profile
            condition.save()
            messages.success(request, 'Medical condition added.')
            return redirect('prescriptions:vault_list')
        messages.error(request, 'Condition was not saved. Check the form errors below.')

    return render(
        request,
        'prescriptions/add_condition.html',
        {'form': form, 'profile': profile},
    )


@login_required
@require_http_methods(['GET', 'POST'])
def prescription_upload_view(request):
    profile = get_active_profile(request)
    if profile is None:
        messages.info(request, 'Select a patient profile first.')
        return redirect('accounts:profile_switch')

    form_data = request.POST if request.method == 'POST' else None
    files_data = request.FILES if request.method == 'POST' else None
    form = PrescriptionUploadForm(
        form_data,
        files_data,
        profile=profile,
    )
    if request.method == 'POST' and form.is_valid():
        prescription = form.save()
        messages.success(request, 'Prescription saved.')
        return redirect(
            'prescriptions:condition_detail',
            condition_pk=prescription.condition_id,
        )
    if request.method == 'POST':
        messages.error(request, 'Prescription was not saved. Check the form errors below.')

    return render(
        request,
        'prescriptions/upload.html',
        {'form': form, 'profile': profile},
    )


@login_required
@require_GET
def condition_detail_view(request, condition_pk):
    profile = get_active_profile(request)
    if profile is None:
        messages.info(request, 'Select a patient profile first.')
        return redirect('accounts:profile_switch')

    condition = get_object_or_404(
        MedicalCondition.objects.filter(profile=profile).prefetch_related(
            'prescriptions__medications',
        ),
        pk=condition_pk,
    )
    return render(
        request,
        'prescriptions/detail.html',
        {'profile': profile, 'condition': condition},
    )


@login_required
@require_GET
def prescription_document_view(request, prescription_pk):
    profile = get_active_profile(request)
    if profile is None:
        messages.info(request, 'Select a patient profile first.')
        return redirect('accounts:profile_switch')

    prescription = get_object_or_404(
        Prescription.objects.filter(condition__profile=profile),
        pk=prescription_pk,
    )
    if not prescription.prescription_file:
        raise Http404('No document is attached to this prescription.')

    response = FileResponse(
        prescription.prescription_file.open('rb'),
        as_attachment=True,
        filename=prescription.prescription_file.name.rsplit('/', 1)[-1],
    )
    response['X-Content-Type-Options'] = 'nosniff'
    return response
