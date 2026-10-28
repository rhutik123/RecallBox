from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Note, Tag


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

    def test_user_cannot_attach_another_users_tag(self):
        other_tag = Tag.objects.create(
            owner=self.user2,
            name="Private tag",
        )
    
        self.client.login(
            username="alice",
            password="test-password-123",
        )

        response = self.client.post(
            reverse("note_create"),
            {
                "title": "Test note",
                "body": "Testing tag ownership",
                "note_type": "text",
                "tags": [other_tag.pk],
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Note.objects.filter(
                owner=self.user1,
                title="Test note",
            ).exists()
        )

class NoteTagTests(TestCase):
    def setUP(self):
        self.user = User.objects.create_user(
            username="tagtester",
            password="test-password-123",
        )
        self.tag1 = Tag.objects.create(
            owner=self.user,
            name="Python",
        )
        self.tag2 = Tag.objects.create(
            owner=self.user,
            name="Django",
        )

        def test_note_can_have_one_tag(self):
            note = Note.objects.create(
                owner = self.user,
                title = "Python Note",
                body = "A Python Note",
            )

            note.tags.add(self.tag1)
            self.assertEqual(note.tags.count(), 1)

        def test_note_can_have_multiple_tags(self):
            note = Note.objects.create(
            owner=self.user,
            title="Development note",
            body="Python and Django",
            )
            
            note.tags.add(self.tag1, self.tag2)
            self.assertEqual(note.tags.count(), 2)