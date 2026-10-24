from datetime import time

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import PatientProfile
from emergency.models import EmergencyContact
from prescriptions.models import MedicalCondition, MedicationItem, Prescription
from reminders.models import CheckupReminder, DoseSchedule
from vitals.models import LifestyleLog, VitalsLog


class AdminPanelTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(
            username='patient-owner',
            email='owner@example.test',
            password='strong-test-password',
        )
        self.profile = PatientProfile.objects.create(
            user=self.owner,
            full_name='Admin Panel Patient',
            blood_group='O+',
        )
        self.staff_user = user_model.objects.create_user(
            username='medhome-staff',
            password='strong-test-password',
            is_staff=True,
        )
        self.url = reverse('admin_panel:dashboard')

    def test_admin_panel_requires_staff_access(self):
        anonymous_response = self.client.get(self.url)
        self.assertRedirects(
            anonymous_response,
            f'{reverse("accounts:login")}?next={self.url}',
        )

        ordinary_user = get_user_model().objects.create_user(
            username='ordinary-user',
            password='strong-test-password',
        )
        self.client.force_login(ordinary_user)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_staff_panel_shows_patient_counts_and_database_guide(self):
        condition = MedicalCondition.objects.create(
            profile=self.profile,
            name='Example condition',
        )
        prescription = Prescription.objects.create(
            condition=condition,
            doctor_name='Care provider',
        )
        medication = MedicationItem.objects.create(
            prescription=prescription,
            medicine_name='Example medicine',
            dosage='1 tablet',
            frequency='Daily',
        )
        VitalsLog.objects.create(profile=self.profile, systolic=120)
        LifestyleLog.objects.create(
            profile=self.profile,
            date=timezone.localdate(),
            water_intake_ml=1500,
        )
        CheckupReminder.objects.create(
            profile=self.profile,
            title='Follow-up',
            due_date=timezone.now(),
        )
        DoseSchedule.objects.create(
            medication=medication,
            profile=self.profile,
            scheduled_time=time(9, 0),
        )
        EmergencyContact.objects.create(
            profile=self.profile,
            name='Emergency contact',
            phone_number='555-0100',
            priority=1,
        )

        self.client.force_login(self.staff_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Patient registry')
        self.assertContains(response, 'Admin Panel Patient')
        self.assertContains(response, 'owner@example.test')
        self.assertContains(response, 'Patient data guide')
        self.assertContains(response, 'Dose schedules')
        profile = response.context['page_obj'].object_list[0]
        self.assertEqual(profile.vitals_count, 1)
        self.assertEqual(profile.lifestyle_count, 1)
        self.assertEqual(profile.active_condition_count, 1)
        self.assertEqual(profile.prescription_count, 1)
        self.assertEqual(profile.medication_count, 1)
        self.assertEqual(profile.checkup_reminder_count, 1)
        self.assertEqual(profile.dose_schedule_count, 1)
        self.assertEqual(profile.emergency_contact_count, 1)
