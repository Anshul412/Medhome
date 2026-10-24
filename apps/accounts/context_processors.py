from .utils import get_active_profile


def medhome_context(request):
    if not request.user.is_authenticated:
        return {'active_profile': None, 'patient_profiles': ()}

    return {
        'active_profile': get_active_profile(request),
        'patient_profiles': request.user.patient_profiles.all(),
    }
