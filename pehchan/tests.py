from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.management import call_command
from datetime import date, timedelta
from io import StringIO
from pehchan.models import Event


class PublicViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_home_page(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_about_page(self):
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)

    def test_public_events_page(self):
        response = self.client.get(reverse('public_events'))
        self.assertEqual(response.status_code, 200)

    def test_volunteer_info_page(self):
        response = self.client.get(reverse('public_volunteer'))
        self.assertEqual(response.status_code, 200)

    def test_donate_info_page(self):
        response = self.client.get(reverse('public_donate'))
        self.assertEqual(response.status_code, 200)

    def test_certificate_verify_page(self):
        response = self.client.get(reverse('public_certificate_verify'))
        self.assertEqual(response.status_code, 200)


class AuthenticationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword123',
            email='testuser@example.com'
        )

    def test_login_page_get(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_signup_page_get(self):
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)

    def test_user_login_valid(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpassword123'
        })
        # Successful login redirects to dashboard
        self.assertEqual(response.status_code, 302)

    def test_user_login_invalid(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)


class EventModelTestCase(TestCase):
    def test_event_status_calculation(self):
        today = date.today()
        upcoming = Event.objects.create(
            name='Future Camp',
            description='Test event',
            event_date=today + timedelta(days=5),
            location='Mumbai'
        )
        self.assertEqual(upcoming.status, 'upcoming')

        past = Event.objects.create(
            name='Past Drive',
            description='Old event',
            event_date=today - timedelta(days=5),
            location='Pune'
        )
        self.assertEqual(past.status, 'completed')


class ManagementCommandTestCase(TestCase):
    def test_create_admin_user_command(self):
        out = StringIO()
        call_command(
            'create_admin_user',
            username='cmdadmin',
            email='cmdadmin@example.com',
            password='cmdpassword123',
            stdout=out
        )
        self.assertTrue(User.objects.filter(username='cmdadmin').exists())
        user = User.objects.get(username='cmdadmin')
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)


from django.core.files.uploadedfile import SimpleUploadedFile
from pehchan.models import PasswordResetOTP, MoneyDonation
from django.utils import timezone


class SecurityVulnerabilitiesTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='secuser',
            email='secuser@example.com',
            password='StrongPassword123!'
        )

    def test_sec01_admin_backdoor_removed(self):
        """SEC-01: Verify /fix-admin-now/ endpoint no longer exists (404)"""
        response = self.client.get('/fix-admin-now/')
        self.assertEqual(response.status_code, 404)

    def test_sec02_prevent_account_enumeration(self):
        """SEC-02: Forgot password returns identical response for existing & non-existing email"""
        # Non-existing user
        res_non_exist = self.client.post(reverse('forgot_password'), {'email': 'ghost@example.com'})
        self.assertEqual(res_non_exist.status_code, 302)
        self.assertRedirects(res_non_exist, reverse('verify_otp'))

        # Session reset
        session = self.client.session
        session.flush()

        # Existing user
        res_exist = self.client.post(reverse('forgot_password'), {'email': 'secuser@example.com'})
        self.assertEqual(res_exist.status_code, 302)
        self.assertRedirects(res_exist, reverse('verify_otp'))

    def test_sec03_otp_flow_enforcement(self):
        """SEC-03: Direct reset without verified OTP is blocked and redirected"""
        # 1. Direct GET or POST to reset_password without session
        response = self.client.get(reverse('reset_password'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('forgot_password'))

        # 2. Session with user_id but otp_verified=False
        session = self.client.session
        session['reset_user_id'] = self.user.id
        session['otp_verified'] = False
        session.save()

        response2 = self.client.get(reverse('reset_password'))
        self.assertEqual(response2.status_code, 302)
        self.assertRedirects(response2, reverse('forgot_password'))

    def test_sec03_expired_otp_rejected(self):
        """SEC-03: Expired OTP is rejected"""
        expired_otp = PasswordResetOTP.objects.create(
            user=self.user,
            otp='123456',
            expires_at=timezone.now() - timedelta(minutes=1)
        )
        session = self.client.session
        session['reset_user_id'] = self.user.id
        session['otp_initiated'] = True
        session.save()

        response = self.client.post(reverse('verify_otp'), {'otp': '123456'})
        self.assertEqual(response.status_code, 200)  # Re-renders with error
        self.assertFalse(self.client.session.get('otp_verified', False))

    def test_sec04_weak_password_rejected_in_reset(self):
        """SEC-04: Weak passwords rejected during password reset"""
        session = self.client.session
        session['reset_user_id'] = self.user.id
        session['otp_verified'] = True
        session.save()

        # Try too short password (< 8 chars)
        response = self.client.post(reverse('reset_password'), {
            'new_password': '123',
            'confirm_password': '123'
        })
        self.assertEqual(response.status_code, 200)
        # User's password should remain unchanged
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('StrongPassword123!'))

    def test_sec06_receipt_upload_security(self):
        """SEC-06: Disallow oversized (>5MB) and dangerous extensions"""
        from pehchan.models import validate_receipt_file
        from django.core.exceptions import ValidationError

        # 1. Dangerous extension (.sh / .exe / .py)
        bad_file = SimpleUploadedFile("malicious.sh", b"echo 'hack'", content_type="text/plain")
        with self.assertRaises(ValidationError):
            validate_receipt_file(bad_file)

        # 2. Oversized file (> 5MB)
        large_content = b"a" * (6 * 1024 * 1024)
        large_file = SimpleUploadedFile("large.png", large_content, content_type="image/png")
        with self.assertRaises(ValidationError):
            validate_receipt_file(large_file)

        # 3. Valid file
        valid_file = SimpleUploadedFile("valid.png", b"fake image bytes", content_type="image/png")
        # Should not raise exception
        validate_receipt_file(valid_file)


class CustomErrorPagesTests(TestCase):
    def setUp(self):
        from django.test import RequestFactory
        self.factory = RequestFactory()

    def test_custom_400_template_rendering(self):
        from pehchan.views import error_400_view
        request = self.factory.get('/some-bad-request')
        response = error_400_view(request)
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, 'Bad Request', status_code=400)
        self.assertContains(response, '400', status_code=400)

    def test_custom_403_template_rendering(self):
        from pehchan.views import error_403_view
        request = self.factory.get('/forbidden')
        response = error_403_view(request)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, '403', status_code=403)

    def test_custom_404_template_rendering(self):
        from pehchan.views import error_404_view
        request = self.factory.get('/nonexistent-page-xyz')
        response = error_404_view(request)
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, '404', status_code=404)

    def test_custom_500_template_rendering(self):
        from pehchan.views import error_500_view
        request = self.factory.get('/server-error')
        response = error_500_view(request)
        self.assertEqual(response.status_code, 500)
        self.assertContains(response, '500', status_code=500)


