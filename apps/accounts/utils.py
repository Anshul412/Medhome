from django.http import HttpRequest

from .models import PatientProfile


def get_active_profile(request: HttpRequest) -> PatientProfile | None:
    profile_id = request.session.get('active_profile_id')
    if profile_id is None:
        return None

    try:
        return PatientProfile.objects.filter(
            user=request.user,
        ).get(pk=profile_id)
    except (PatientProfile.DoesNotExist, ValueError, TypeError):
        request.session.pop('active_profile_id', None)
        return None
