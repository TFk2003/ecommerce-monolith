from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient


User = get_user_model()


class UserProfileEndpointTest(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.user = User.objects.create_user(
			username='profile@test.com',
			email='profile@test.com',
			password='testpass123',
			name='Profile User',
		)

	def test_get_profile_creates_missing_profile(self):
		self.client.force_authenticate(user=self.user)

		response = self.client.get('/api/user/profile/')

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn('profile', response.data)

	def test_patch_profile_does_not_500_without_existing_profile(self):
		self.client.force_authenticate(user=self.user)

		response = self.client.patch(
			'/api/user/profile/',
			{'name': 'Updated Profile User'},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['name'], 'Updated Profile User')
		self.assertIn('profile', response.data)
		self.user.refresh_from_db()
		self.assertEqual(self.user.name, 'Updated Profile User')
		self.assertTrue(hasattr(self.user, 'user_profile'))


class UserAdminUpdateTest(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.admin = User.objects.create_user(
			username='admin@test.com',
			email='admin@test.com',
			password='testpass123',
			name='Admin User',
			is_staff=True,
		)
		self.user = User.objects.create_user(
			username='target@test.com',
			email='target@test.com',
			password='testpass123',
			name='Target User',
		)

	def test_admin_can_update_user_profile_with_long_mobile(self):
		self.client.force_authenticate(user=self.admin)

		response = self.client.patch(
			f'/api/user/update/{self.user.id}/',
			{
				'name': 'Target User',
				'email': 'target@test.com',
				'profile': {
					'mobile': '03568956495',
					'gender': 'M',
				},
				'is_admin': True,
			},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.user.refresh_from_db()
		self.assertEqual(self.user.user_profile.mobile, '03568956495')
		self.assertTrue(self.user.is_staff)
