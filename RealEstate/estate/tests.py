from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Profile, RealEstate

class EstateModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testadmin', password='password')
        Profile.objects.create(user=self.user, role='admin')
        self.estate = RealEstate.objects.create(
            title='Test Flat', area=50.0, location='Moscow', price=10000, owner=self.user
        )

    def test_estate_creation(self):
        self.assertEqual(self.estate.title, 'Test Flat')
        self.assertEqual(self.estate.status, 'available')

    def test_dashboard_access(self):
        client = Client()
        client.login(username='testadmin', password='password')
        response = client.get('/estate/dashboard/')
        self.assertEqual(response.status_code, 200)