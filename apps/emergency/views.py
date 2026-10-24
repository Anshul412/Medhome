import re
import uuid
from uuid import UUID

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from accounts.models import PatientProfile
from accounts.utils import get_active_profile

from .models import EmergencyContact


def _tel_target(value):
    normalized = re.sub(r'\D', '', value)
    if not normalized:
        return ''
    return f'+{normalized}' if value.strip().startswith('+') else normalized


@login_required
@require_GET
def sos_dashboard_view(request):
    profile = get_active_profile(request)
    if profile is None:
        messages.info(request, 'Select a patient profile first.')
        return redirect('accounts:profile_switch')

    contacts = [
        {
            'contact': contact,
            'tel_target': _tel_target(contact.phone_number),
        }
        for contact in EmergencyContact.objects.filter(
            profile=profile,
        ).order_by('priority', 'pk')
    ]
    emergency_number = _tel_target(
        getattr(settings, 'MEDHOME_EMERGENCY_NUMBER', '112'),
    )
    primary_contact = contacts[0] if contacts else None
    return render(
        request,
        'emergency/sos.html',
        {
            'profile': profile,
            'contacts': contacts,
            'primary_contact': primary_contact,
            'emergency_number': emergency_number,
            'ambulance_numbers': ('108', '112'),
            'ice_url': request.build_absolute_uri(
                reverse('emergency:ice', kwargs={'token': profile.ice_token}),
            ),
        },
    )


@require_GET
def public_ice_view(request, token: UUID):
    profile = get_object_or_404(
        PatientProfile.objects.prefetch_related('emergency_contacts'),
        ice_token=token,
    )
    contacts = [
        {
            'contact': contact,
            'tel_target': _tel_target(contact.phone_number),
        }
        for contact in profile.emergency_contacts.all()
    ]
    response = render(
        request,
        'emergency/ice_profile.html',
        {
            'profile': profile,
            'contacts': contacts,
        },
    )
    response['Cache-Control'] = 'private, no-store'
    response['X-Robots-Tag'] = 'noindex, nofollow'
    response['Referrer-Policy'] = 'no-referrer'
    return response


@login_required
@require_POST
def rotate_ice_token_view(request):
    profile = get_active_profile(request)
    if profile is None:
        messages.info(request, 'Select a patient profile first.')
        return redirect('accounts:profile_switch')

    profile.ice_token = uuid.uuid4()
    profile.save(update_fields=('ice_token',))
    messages.success(request, 'The public ICE link was rotated; the old link no longer works.')
    return redirect('emergency:dashboard')
