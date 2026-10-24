from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import PatientProfile
from emergency.models import EmergencyContact
from prescriptions.models import MedicalCondition
from vitals.models import VitalsLog


class MedHomeEndToEndFlowTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='flow-user',
            email='flow-user@example.test',
            password='Flow-test-password-5482!',
        )
        self.profile = PatientProfile.objects.create(
            user=self.user,
            full_name='Flow Test Patient',
            blood_group='O+',
            chronic_conditions='Test condition',
            emergency_notes='Test emergency note',
        )
        self.client.force_login(self.user)
        session = self.client.session
        session['active_profile_id'] = self.profile.pk
        session.save()

    def test_root_landing_page_and_authenticated_dashboard_redirect(self):
        anonymous_client = Client()
        landing_response = anonymous_client.get(reverse('home'))

        self.assertEqual(landing_response.status_code, 200)
        self.assertContains(
            landing_response,
            'Hospital-Grade Care,',
        )
        self.assertContains(landing_response, 'Access Portal')
        self.assertContains(landing_response, 'Register Family')
        self.assertContains(
            landing_response,
            f'href="{reverse("admin:login")}"',
        )
        self.assertContains(landing_response, 'Admin Login')

        dashboard_response = self.client.get(reverse('home'))
        self.assertRedirects(
            dashboard_response,
            reverse('vitals:dashboard'),
        )

    def test_patient_profiles_in_admin_require_staff_and_model_permissions(self):
        patient_changelist_url = reverse(
            'admin:accounts_patientprofile_changelist',
        )
        anonymous_client = Client()
        self.assertEqual(
            anonymous_client.get(patient_changelist_url).status_code,
            302,
        )

        non_staff_response = self.client.get(patient_changelist_url)
        self.assertEqual(non_staff_response.status_code, 302)
        self.assertIn(reverse('admin:login'), non_staff_response.url)

        unprivileged_staff = get_user_model().objects.create_user(
            username='unprivileged-staff',
            password='Staff-test-password-6383!',
            is_staff=True,
        )
        unprivileged_client = Client()
        unprivileged_client.force_login(unprivileged_staff)
        self.assertEqual(
            unprivileged_client.get(patient_changelist_url).status_code,
            403,
        )

        staff_user = get_user_model().objects.create_user(
            username='authorized-staff',
            password='Staff-test-password-6382!',
            is_staff=True,
        )
        staff_user.user_permissions.set(
            Permission.objects.filter(
                content_type__app_label='accounts',
                codename__in=(
                    'add_patientprofile',
                    'change_patientprofile',
                    'delete_patientprofile',
                    'view_patientprofile',
                ),
            ),
        )
        staff_client = Client()
        staff_client.force_login(staff_user)

        response = staff_client.get(patient_changelist_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'MedHome Database')
        self.assertContains(response, 'css/admin.css')
        self.assertContains(response, 'Flow Test Patient')
        change_url = reverse(
            'admin:accounts_patientprofile_change',
            args=(self.profile.pk,),
        )
        self.assertEqual(staff_client.get(change_url).status_code, 200)
        update_response = staff_client.post(change_url, {
            '_save': 'Save',
            'user': self.user.pk,
            'full_name': 'Updated Admin Patient',
            'relationship': 'Self',
            'dob': '',
            'blood_group': 'O+',
            'chronic_conditions': 'Admin managed condition',
            'emergency_notes': '',
        })
        self.assertEqual(update_response.status_code, 302)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.full_name, 'Updated Admin Patient')

    def test_admin_dashboard_uses_medhome_database_branding_and_record_cards(self):
        staff_user = get_user_model().objects.create_superuser(
            username='dashboard-admin',
            email='dashboard-admin@example.test',
            password='Dashboard-test-password-8512!',
        )
        staff_client = Client()
        staff_client.force_login(staff_user)

        response = staff_client.get(reverse('admin:index'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<title>Healthcare records | MedHome Database</title>', html=True)
        self.assertContains(response, 'MedHome Database')
        self.assertContains(response, 'Patient profiles')
        self.assertContains(response, 'Healthcare records')
        self.assertContains(response, 'css/admin.css')

    def test_user_signup_login_and_profile_creation(self):
        client = Client()
        signup_response = client.post(
            reverse('accounts:signup'),
            {
                'username': 'new-flow-user',
                'first_name': 'Test',
                'last_name': 'User',
                'email': 'new-flow-user@example.test',
                'phone_number': '5551234567',
                'password1': 'Flow-test-password-9911!',
                'password2': 'Flow-test-password-9911!',
            },
        )

        self.assertEqual(signup_response.status_code, 302)
        new_user = get_user_model().objects.get(username='new-flow-user')
        self.assertTrue(client.session.get('_auth_user_id'))
        self.assertEqual(int(client.session['_auth_user_id']), new_user.pk)

        profile_response = client.post(
            reverse('accounts:profile_create'),
            {
                'full_name': 'New Flow Patient',
                'relationship': 'Self',
                'dob': '',
                'blood_group': 'O+',
                'chronic_conditions': '',
                'emergency_notes': '',
            },
        )

        self.assertEqual(profile_response.status_code, 302)
        profile = PatientProfile.objects.get(full_name='New Flow Patient')
        self.assertEqual(profile.user, new_user)
        self.assertEqual(client.session['active_profile_id'], profile.pk)

        client.post(reverse('accounts:logout'))
        login_response = client.post(
            reverse('accounts:login'),
            {
                'username': 'new-flow-user',
                'password': 'Flow-test-password-9911!',
            },
        )
        self.assertEqual(login_response.status_code, 302)
        self.assertTrue(client.session.get('_auth_user_id'))

    def test_vitals_post_redirects_and_persists_exact_submitted_values(self):
        submitted_recorded_at = timezone.localtime().replace(
            second=0,
            microsecond=0,
        )
        response = self.client.post(
            reverse('vitals:dashboard'),
            {
                'form_name': 'vitals',
                'vitals-recorded_at': submitted_recorded_at.strftime(
                    '%Y-%m-%dT%H:%M',
                ),
                'vitals-systolic': '123',
                'vitals-diastolic': '82',
                'vitals-pulse': '71',
                'vitals-spo2': '97.5',
                'vitals-blood_glucose': '5.25',
                'vitals-notes': 'End-to-end test reading',
            },
        )

        self.assertEqual(response.status_code, 302)
        entry = VitalsLog.objects.get(
            profile=self.profile,
            notes='End-to-end test reading',
        )
        self.assertEqual(entry.systolic, 123)
        self.assertEqual(entry.diastolic, 82)
        self.assertEqual(entry.pulse, 71)
        self.assertEqual(entry.spo2, Decimal('97.50'))
        self.assertEqual(entry.blood_glucose, Decimal('5.25'))
        self.assertEqual(
            timezone.localtime(entry.recorded_at),
            submitted_recorded_at,
        )

    def test_medical_condition_form_post_binds_profile_and_persists(self):
        response = self.client.post(
            reverse('prescriptions:add_condition'),
            {
                'name': 'Hypertension',
                'diagnosed_date': timezone.localdate().isoformat(),
                'is_active': 'on',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('prescriptions:vault_list'))
        saved_condition = MedicalCondition.objects.get(name='Hypertension')
        self.assertEqual(saved_condition.profile, self.profile)
        self.assertTrue(saved_condition.is_active)

    def test_invalid_medical_condition_submission_renders_form_errors(self):
        response = self.client.post(
            reverse('prescriptions:add_condition'),
            {
                'name': '',
                'diagnosed_date': 'not-a-date',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Condition was not saved')
        self.assertContains(response, 'This field is required')
        self.assertFalse(MedicalCondition.objects.filter(profile=self.profile).exists())

    def test_vault_lists_active_and_past_conditions_for_active_profile(self):
        active = MedicalCondition.objects.create(
            profile=self.profile,
            name='Active condition',
            is_active=True,
        )
        past = MedicalCondition.objects.create(
            profile=self.profile,
            name='Past condition',
            is_active=False,
        )
        foreign_profile = PatientProfile.objects.create(
            user=get_user_model().objects.create_user(username='vault-other'),
            full_name='Other patient',
        )
        MedicalCondition.objects.create(
            profile=foreign_profile,
            name='Another patient condition',
        )

        response = self.client.get(reverse('prescriptions:vault_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, active.name)
        self.assertContains(response, past.name)
        self.assertNotContains(response, 'Another patient condition')

    def test_chart_data_endpoint_returns_required_json_arrays(self):
        VitalsLog.objects.create(
            profile=self.profile,
            systolic=123,
            diastolic=82,
            spo2=Decimal('97.50'),
            blood_glucose=Decimal('5.25'),
        )

        response = self.client.get('/vitals/api/chart-data/')

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        for key in ('dates', 'systolic', 'diastolic', 'spo2'):
            with self.subTest(array=key):
                self.assertIn(key, payload)
                self.assertIsInstance(payload[key], list)
        self.assertEqual(payload['systolic'], [123])
        self.assertEqual(payload['diastolic'], [82])
        self.assertEqual(payload['spo2'], [97.5])

    def test_authenticated_sos_and_anonymous_public_ice_routes(self):
        EmergencyContact.objects.create(
            profile=self.profile,
            name='Flow Test Contact',
            relationship='Family',
            phone_number='+1 555 123 4567',
            priority=1,
        )

        sos_response = self.client.get(reverse('emergency:dashboard'))
        self.assertEqual(sos_response.status_code, 200)
        self.assertContains(sos_response, 'Flow Test Contact')
        self.assertContains(sos_response, 'tel:108')
        self.assertContains(sos_response, 'tel:112')

        anonymous_client = Client()
        ice_response = anonymous_client.get(
            reverse('emergency:ice', kwargs={'token': self.profile.ice_token}),
        )
        self.assertEqual(ice_response.status_code, 200)
        self.assertContains(ice_response, 'Flow Test Patient')
        self.assertContains(ice_response, 'O+')
        self.assertContains(ice_response, 'Test emergency note')
        self.assertContains(ice_response, 'Flow Test Contact')
