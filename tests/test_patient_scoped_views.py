from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile

from emergency.models import EmergencyContact
from prescriptions.models import MedicalCondition, MedicationItem, Prescription
from reminders.models import CheckupReminder, DoseSchedule
from vitals.models import LifestyleLog, VitalsLog

from accounts.models import PatientProfile


class PatientScopedViewsTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='owner',
            email='private-owner@example.test',
            password='a-strong-test-password',
        )
        self.other_user = user_model.objects.create_user(
            username='other',
            password='a-strong-test-password',
        )
        self.profile = PatientProfile.objects.create(
            user=self.user,
            full_name='Profile One',
            blood_group='O+',
            chronic_conditions='Approved ICE condition',
            emergency_notes='Approved ICE note',
        )
        self.other_profile = PatientProfile.objects.create(
            user=self.other_user,
            full_name='Private Other Profile',
        )
        session = self.client.session
        session['active_profile_id'] = self.profile.pk
        session.save()
        self.client.force_login(self.user)

    def test_signup_profile_creation_login_and_logout_flow(self):
        anonymous = self.client_class()
        signup_url = reverse('accounts:signup')
        self.assertEqual(anonymous.get(signup_url).status_code, 200)

        response = anonymous.post(signup_url, {
            'username': 'newuser',
            'email': 'newuser@example.test',
            'phone_number': '',
            'password1': 'MedHome-random-test-password-4908!',
            'password2': 'MedHome-random-test-password-4908!',
        })
        self.assertRedirects(response, reverse('accounts:profile_create'))

        response = anonymous.post(reverse('accounts:profile_create'), {
            'full_name': 'New Patient',
            'relationship': 'Self',
            'dob': '',
            'blood_group': 'unknown',
            'chronic_conditions': '',
            'emergency_notes': '',
        })
        self.assertRedirects(response, reverse('accounts:profile_switch'))
        created_profile = PatientProfile.objects.get(full_name='New Patient')
        self.assertEqual(
            anonymous.session['active_profile_id'],
            created_profile.pk,
        )

        self.assertRedirects(
            anonymous.post(reverse('accounts:logout')),
            reverse('accounts:login'),
        )
        self.assertRedirects(
            anonymous.post(reverse('accounts:login'), {
                'username': 'newuser',
                'password': 'MedHome-random-test-password-4908!',
            }),
            reverse('accounts:profile_switch'),
        )

    def test_active_profile_pages_render(self):
        urls = (
            'accounts:profile_create',
            'accounts:profile_switch',
            'accounts:profile_detail',
            'vitals:log',
            'prescriptions:upload',
            'emergency:dashboard',
        )
        for url_name in urls:
            with self.subTest(url_name=url_name):
                self.assertEqual(
                    self.client.get(reverse(url_name)).status_code,
                    200,
                )

    def test_patient_profile_displays_active_profile_and_allows_owner_edit(self):
        response = self.client.get(reverse('accounts:profile_detail'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Patient Profile')
        self.assertContains(response, 'Profile One')
        self.assertContains(response, 'Approved ICE condition')

        edit_url = reverse(
            'accounts:profile_edit',
            args=(self.profile.pk,),
        )
        response = self.client.post(edit_url, {
            'full_name': 'Updated Profile One',
            'relationship': 'Self',
            'dob': '',
            'blood_group': 'O+',
            'chronic_conditions': 'Updated condition',
            'emergency_notes': 'Updated emergency note',
        })
        self.assertRedirects(response, reverse('accounts:profile_detail'))
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.full_name, 'Updated Profile One')
        self.assertEqual(self.profile.chronic_conditions, 'Updated condition')

    def test_patient_profile_edit_cannot_access_another_users_profile(self):
        response = self.client.get(
            reverse(
                'accounts:profile_edit',
                args=(self.other_profile.pk,),
            ),
        )
        self.assertEqual(response.status_code, 404)

    def test_vitals_dashboard_displays_latest_readings_and_spo2_warning(self):
        VitalsLog.objects.create(
            profile=self.profile,
            recorded_at=timezone.now(),
            systolic=120,
            diastolic=80,
            pulse=72,
            spo2=93,
            blood_glucose=5.4,
        )

        response = self.client.get(reverse('vitals:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '120/80 mmHg')
        self.assertContains(response, '93 %')
        self.assertContains(response, 'Below 94%')
        self.assertContains(response, '72 bpm')
        self.assertContains(response, 'bp-chart')
        self.assertContains(response, 'Blood glucose')

    def test_sos_dashboard_renders_call_services_and_profile_ice_details(self):
        EmergencyContact.objects.create(
            profile=self.profile,
            name='Primary Contact',
            phone_number='+1 (555) 222-3333',
            priority=1,
        )

        response = self.client.get(reverse('emergency:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'tel:108')
        self.assertContains(response, 'tel:112')
        self.assertContains(response, 'tel:+15552223333')
        self.assertContains(response, 'Blood group')
        self.assertContains(response, 'Approved ICE note')
        self.assertContains(response, 'Share Location via WhatsApp')

    def test_chart_data_is_limited_to_active_profile(self):
        now = timezone.now()
        VitalsLog.objects.create(
            profile=self.profile,
            recorded_at=now,
            systolic=120,
            diastolic=80,
            spo2=98,
            blood_glucose=5.4,
        )
        VitalsLog.objects.create(
            profile=self.other_profile,
            recorded_at=now,
            systolic=190,
        )

        response = self.client.get(reverse('vitals:chart_data'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['systolic'], [120])
        self.assertEqual(response.json()['diastolic'], [80])
        self.assertEqual(response.json()['spo2'], [98.0])
        self.assertEqual(response.json()['blood_glucose'], [5.4])
        chart_route = self.client.get('/vitals/api/chart-data/')
        self.assertEqual(chart_route.status_code, 200)

    def test_vitals_and_lifestyle_forms_save_profile_foreign_keys(self):
        dashboard = self.client.get(reverse('vitals:dashboard'))
        self.assertContains(dashboard, 'name="vitals-recorded_at"')
        self.assertContains(dashboard, 'name="lifestyle-date"')

        vitals_response = self.client.post(reverse('vitals:dashboard'), {
            'form_name': 'vitals',
            'vitals-recorded_at': timezone.localtime().strftime('%Y-%m-%dT%H:%M'),
            'vitals-systolic': '121',
            'vitals-diastolic': '81',
            'vitals-pulse': '72',
            'vitals-spo2': '98',
            'vitals-blood_glucose': '5.4',
            'vitals-notes': 'Test entry',
        })
        self.assertRedirects(vitals_response, reverse('vitals:log'))
        self.assertTrue(
            VitalsLog.objects.filter(
                profile=self.profile,
                systolic=121,
                notes='Test entry',
            ).exists()
        )

        lifestyle_response = self.client.post(reverse('vitals:dashboard'), {
            'form_name': 'lifestyle',
            'lifestyle-date': timezone.localdate().isoformat(),
            'lifestyle-water_intake_ml': '1800',
            'lifestyle-calories_kcal': '2100',
        })
        self.assertRedirects(lifestyle_response, reverse('vitals:log'))
        self.assertTrue(
            LifestyleLog.objects.filter(
                profile=self.profile,
                water_intake_ml=1800,
                calories_kcal=2100,
            ).exists()
        )

    def test_unidentified_or_invalid_vitals_submission_shows_error(self):
        empty = self.client.post(reverse('vitals:dashboard'), {})
        self.assertContains(empty, 'submitted form could not be identified')
        self.assertContains(empty, 'This field is required')

        unidentified = self.client.post(
            reverse('vitals:dashboard'),
            {'vitals-systolic': '120'},
        )
        self.assertContains(unidentified, 'submitted form could not be identified')
        self.assertEqual(VitalsLog.objects.count(), 0)

        invalid = self.client.post(reverse('vitals:dashboard'), {
            'form_name': 'vitals',
            'vitals-recorded_at': timezone.localtime().strftime('%Y-%m-%dT%H:%M'),
            'vitals-systolic': 'not-a-number',
            'vitals-diastolic': '80',
            'vitals-pulse': '',
            'vitals-spo2': '',
            'vitals-blood_glucose': '',
            'vitals-notes': '',
        })
        self.assertContains(invalid, 'Vitals were not saved')
        self.assertContains(invalid, 'Enter a whole number')
        self.assertEqual(VitalsLog.objects.count(), 0)

    def test_prescription_upload_saves_file_and_condition_relationship(self):
        condition = MedicalCondition.objects.create(
            profile=self.profile,
            name='Upload test condition',
        )
        with TemporaryDirectory() as media_directory:
            with override_settings(MEDIA_ROOT=media_directory):
                upload = SimpleUploadedFile(
                    'test-prescription.pdf',
                    b'%PDF-1.4 test content',
                    content_type='application/pdf',
                )
                response = self.client.post(
                    reverse('prescriptions:upload'),
                    {
                        'condition': str(condition.pk),
                        'doctor_name': 'Test Doctor',
                        'clinic_name': 'Test Clinic',
                        'issued_date': timezone.localdate().isoformat(),
                        'notes': 'Upload test',
                        'prescription_file': upload,
                    },
                )

                self.assertRedirects(
                    response,
                    reverse(
                        'prescriptions:condition_detail',
                        args=(condition.pk,),
                    ),
                )
                prescription = Prescription.objects.get(
                    condition=condition,
                    doctor_name='Test Doctor',
                )
                self.assertTrue(prescription.prescription_file)
                self.assertTrue(
                    Path(media_directory, prescription.prescription_file.name).is_file()
                )

    def test_medical_and_reminder_views_are_limited_to_active_profile(self):
        own_condition = MedicalCondition.objects.create(
            profile=self.profile,
            name='Own condition',
        )
        MedicalCondition.objects.create(
            profile=self.other_profile,
            name='Private condition',
        )
        own_prescription = Prescription.objects.create(condition=own_condition)
        own_medication = MedicationItem.objects.create(
            prescription=own_prescription,
            medicine_name='Own medicine',
            dosage='1 tablet',
            frequency='daily',
        )
        DoseSchedule.objects.create(
            medication=own_medication,
            profile=self.profile,
            scheduled_time='09:00',
        )
        CheckupReminder.objects.create(
            profile=self.profile,
            title='Own checkup',
            due_date=timezone.now() + timedelta(days=1),
        )
        CheckupReminder.objects.create(
            profile=self.other_profile,
            title='Private checkup',
            due_date=timezone.now() + timedelta(days=1),
        )

        vault = self.client.get(reverse('prescriptions:list'))
        reminders = self.client.get(reverse('reminders:dashboard'))

        self.assertContains(vault, 'Own condition')
        self.assertNotContains(vault, 'Private condition')
        self.assertContains(reminders, 'Own checkup')
        self.assertNotContains(reminders, 'Private checkup')

    def test_dose_toggle_cannot_access_another_profiles_dose(self):
        condition = MedicalCondition.objects.create(
            profile=self.profile,
            name='Medication condition',
        )
        prescription = Prescription.objects.create(condition=condition)
        medication = MedicationItem.objects.create(
            prescription=prescription,
            medicine_name='Medication',
            dosage='1 tablet',
            frequency='daily',
        )
        foreign_dose = DoseSchedule.objects.create(
            medication=medication,
            profile=self.other_profile,
            scheduled_time='09:00',
        )
        url = reverse('reminders:toggle_dose', args=(foreign_dose.pk,))

        self.assertEqual(self.client.post(url).status_code, 404)

        own_dose = DoseSchedule.objects.create(
            medication=medication,
            profile=self.profile,
            scheduled_time='10:00',
        )
        response = self.client.post(
            reverse('reminders:toggle_dose', args=(own_dose.pk,)),
            HTTP_ACCEPT='application/json',
        )
        own_dose.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(own_dose.is_taken_today)
        self.assertTrue(response.json()['is_taken'])

    def test_public_ice_view_shows_only_approved_profile_fields(self):
        EmergencyContact.objects.create(
            profile=self.profile,
            name='ICE Contact',
            phone_number='+1 (555) 111-2222',
            priority=1,
        )
        anonymous_client = self.client_class()

        response = anonymous_client.get(
            reverse('emergency:ice', kwargs={'token': self.profile.ice_token}),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Profile One')
        self.assertContains(response, 'Approved ICE condition')
        self.assertContains(response, 'Approved ICE note')
        self.assertContains(response, 'ICE Contact')
        self.assertNotContains(response, 'private-owner@example.test')
        self.assertEqual(response['Cache-Control'], 'private, no-store')

    def test_ice_link_rotation_invalidates_the_previous_token(self):
        old_token = self.profile.ice_token
        rotate_url = reverse('emergency:rotate_ice_token')

        self.assertEqual(self.client.get(rotate_url).status_code, 405)
        response = self.client.post(rotate_url)

        self.profile.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertNotEqual(self.profile.ice_token, old_token)
        self.assertEqual(
            self.client.get(
                reverse('emergency:ice', kwargs={'token': old_token}),
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.get(
                reverse('emergency:ice', kwargs={'token': self.profile.ice_token}),
            ).status_code,
            200,
        )
