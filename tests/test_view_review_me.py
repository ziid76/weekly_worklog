from datetime import date
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse


class ReviewMeViewTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username="bob", password="secret")
        self.client = Client()
        self.url = reverse("app:review_me")

    def test_requires_login(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    @patch("app.views.review_last_4_weeks")
    def test_returns_json_payload(self, mock_service: MagicMock) -> None:
        mock_service.return_value = {"summary": "ok"}
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.json(), {"summary": "ok"})
        mock_service.assert_called_once_with(self.user, as_of=None)

    @patch("app.views.review_last_4_weeks")
    def test_rejects_non_get(self, mock_service: MagicMock) -> None:
        self.client.force_login(self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 405)
        mock_service.assert_not_called()

    @patch("app.views.review_last_4_weeks")
    def test_rejects_invalid_as_of(self, mock_service: MagicMock) -> None:
        self.client.force_login(self.user)
        response = self.client.get(self.url, {"as_of": "not-a-date"})
        self.assertEqual(response.status_code, 400)
        mock_service.assert_not_called()

    @patch("app.views.review_last_4_weeks")
    def test_calls_service_with_as_of(self, mock_service: MagicMock) -> None:
        mock_service.return_value = {"summary": "ok"}
        self.client.force_login(self.user)
        response = self.client.get(self.url, {"as_of": "2024-06-30"})
        self.assertEqual(response.status_code, 200)
        mock_service.assert_called_once()
        _args, kwargs = mock_service.call_args
        self.assertEqual(kwargs["as_of"], date(2024, 6, 30))
