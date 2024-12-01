from rest_framework.test import APIClient
from django.test import TestCase
from django.contrib.auth.models import User
from .models import Customer


class CustomerPasswordUpdateTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="johan", password="azer1234"
        )
        self.customer = Customer.objects.create(user=self.user, email="johan@gmail.com")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_update_password_and_login(self):
        # Mise à jour du mot de passe
        response = self.client.patch(
            f"/customers/{self.customer.customer_id}/",
            {"user": {"password": "azer12345"}},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        # Déconnexion et tentative de connexion avec le nouveau mot de passe
        self.client.logout()
        response = self.client.post(
            "/api/token/",
            {"username": "johan", "password": "azer12345"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
