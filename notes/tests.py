from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Note


User = get_user_model()


class NoteOwnershipTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username="alice",
            password="test-password-123",
        )
        self.user2 = User.objects.create_user(
            username="bob",
            password="test-password-123",
        )

        self.note = Note.objects.create(
            owner=self.user1,
            title="Alice private note",
            body="Only Alice should see this.",
            note_type=Note.NoteType.TEXT,
        )

    def test_home_requires_login(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 302)

    def test_user_sees_only_own_notes(self):
        self.client.login(
            username="bob",
            password="test-password-123",
        )

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Alice private note")

    def test_user_cannot_edit_another_users_note(self):
        self.client.login(
            username="bob",
            password="test-password-123",
        )

        response = self.client.get(
            reverse("note_update", args=[self.note.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_user_cannot_delete_another_users_note(self):
        self.client.login(
            username="bob",
            password="test-password-123",
        )

        response = self.client.post(
            reverse("note_delete", args=[self.note.pk])
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(
            Note.objects.filter(pk=self.note.pk).exists()
        )