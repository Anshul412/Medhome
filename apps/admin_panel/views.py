from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import render
from django.views.decorators.http import require_GET

from accounts.models import CustomUser, PatientProfile
from emergency.models import EmergencyContact
from prescriptions.models import MedicalCondition, MedicationItem, Prescription
from reminders.models import CheckupReminder, DoseSchedule
from vitals.models import LifestyleLog, VitalsLog


@login_required
@require_GET
def dashboard(request):
    if not request.user.is_staff:
        raise PermissionDenied

    datasets = [
        {
            'name': 'User accounts',
            'count': CustomUser.objects.count(),
            'description': 'Login and contact details, caregiver status, and the account that owns each patient profile.',
            'fields': 'Username, name, email, phone number, caregiver/staff status.',
        },
        {
            'name': 'Patient profiles',
            'count': PatientProfile.objects.count(),
            'description': 'Patient identity and basic care context. Each profile belongs to one user account.',
            'fields': 'Full name, relationship, date of birth, blood group, chronic conditions, emergency notes, ICE token, created/updated dates.',
        },
        {
            'name': 'Vital readings',
            'count': VitalsLog.objects.count(),
            'description': 'Time-stamped measurements entered for a patient profile.',
            'fields': 'Systolic/diastolic blood pressure, pulse, SpO2, blood glucose, notes, recorded date/time.',
        },
        {
            'name': 'Lifestyle logs',
            'count': LifestyleLog.objects.count(),
            'description': 'Daily wellness totals; each patient can have one entry per date.',
            'fields': 'Date, water intake (ml), calories (kcal).',
        },
        {
            'name': 'Medical conditions',
            'count': MedicalCondition.objects.count(),
            'description': 'Diagnoses linked directly to a patient profile. Prescriptions are grouped under a condition.',
            'fields': 'Condition name, diagnosis date, active status.',
        },
        {
            'name': 'Prescriptions',
            'count': Prescription.objects.count(),
            'description': 'Prescription records linked to a condition, including optional uploaded files.',
            'fields': 'Doctor, clinic, issued date, file, notes.',
        },
        {
            'name': 'Medication items',
            'count': MedicationItem.objects.count(),
            'description': 'Medicines recorded on prescriptions; dose schedules can refer to these items.',
            'fields': 'Medicine name, dosage, frequency, meal relation, duration.',
        },
        {
            'name': 'Checkup reminders',
            'count': CheckupReminder.objects.count(),
            'description': 'Appointments and checkups linked to a patient profile.',
            'fields': 'Title, doctor/lab, due date, recurrence, completion status.',
        },
        {
            'name': 'Dose schedules',
            'count': DoseSchedule.objects.count(),
            'description': 'Medication times and taken status, linked to both a medication and its patient profile.',
            'fields': 'Scheduled time, taken status, last taken date/time.',
        },
        {
            'name': 'Emergency contacts',
            'count': EmergencyContact.objects.count(),
            'description': 'Ordered emergency contacts linked to a patient profile.',
            'fields': 'Name, relationship, phone number, priority.',
        },
    ]

    profiles = PatientProfile.objects.select_related('user').annotate(
        vitals_count=Count('vitals_logs', distinct=True),
        lifestyle_count=Count('lifestyle_logs', distinct=True),
        condition_count=Count('medical_conditions', distinct=True),
        active_condition_count=Count(
            'medical_conditions',
            filter=Q(medical_conditions__is_active=True),
            distinct=True,
        ),
        prescription_count=Count(
            'medical_conditions__prescriptions',
            distinct=True,
        ),
        medication_count=Count(
            'medical_conditions__prescriptions__medications',
            distinct=True,
        ),
        checkup_reminder_count=Count('checkup_reminders', distinct=True),
        dose_schedule_count=Count('dose_schedules', distinct=True),
        emergency_contact_count=Count('emergency_contacts', distinct=True),
    ).order_by('full_name', 'pk')
    page_obj = Paginator(profiles, 20).get_page(request.GET.get('page'))

    return render(request, 'admin_panel/dashboard.html', {
        'datasets': datasets,
        'page_obj': page_obj,
    })
