from django.contrib.auth import get_user_model
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
    def setUp(self):
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
            owner=self.user,
            title="Python Note",
            body="A Python note",
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


class NoteSearchTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
        username="searchuser",
        password="test-password-123",
        )

        Note.objects.create(
            owner=self.user,
            title="Python tutorial",
            body="Learn programming basics",
        )

        Note.objects.create(
            owner=self.user,
            title="Django guide",
            body="Learn Python web development",
        )

        Note.objects.create(
            owner=self.user,
            title="Shopping list",
            body="Buy milk and bread",
        )

        self.client.login(
        username="searchuser",
        password="test-password-123",
        )

        def test_search_finds_note_by_title(self):
            response = self.client.get(reverse("home"), {"q", "web development"})

            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Django guide")
            self.assertNotContains(response, "Shopping list")

        def test_search_with_no_matches(self):
            response = self.client.get(
                reverse("home"),
                {"q": "something-that-does-not-exist"},
            )

            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "No matching notes")
            self.assertNotContains(response, "Python tutorial")

    def test_search_combined_with_note_type_and_tag(self):
        tag = Tag.objects.create(
            owner=self.user,
            name="Django",
        )

        matching_note = Note.objects.create(
            owner=self.user,
            title="Python web tutorial",
            body="Build a web application",
            note_type=Note.NoteType.TEXT,
        )
        matching_note.tags.add(tag)

        wrong_type_note = Note.objects.create(
            owner=self.user,
            title="Python code example",
            body="Build a web application",
            note_type=Note.NoteType.CODE,
        )
        wrong_type_note.tags.add(tag)

        wrong_tag_note = Note.objects.create(
            owner=self.user,
            title="Python web reference",
            body="Build a web application",
            note_type=Note.NoteType.TEXT,
        )

        response = self.client.get(
            reverse("home"),
            {
                "q": "Python",
                "tag": str(tag.pk),
                "type": "text",
                "archived": "false",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Python web tutorial")
        self.assertNotContains(response, "Python code example")
        self.assertNotContains(response, "Python web reference")

    def test_pagination_shows_ten_notes_per_page(self):
        for i in range(12):
            Note.objects.create(
                owner=self.user,
                title=f"Pagination note {i}",
                body=f"Body for note {i}",
            )

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["page_obj"]), 10)
        self.assertEqual(response.context["page_obj"].paginator.num_pages, 2)

    def test_pagination_can_open_second_page(self):
        for i in range(12):
            Note.objects.create(
                owner=self.user,
                title=f"Pagination note {i}",
                body=f"Body for note {i}",
            )

        response = self.client.get(
            reverse("home"),
            {"page": 2},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].number, 2)
        self.assertLessEqual(len(response.context["page_obj"]), 10)

    def test_pagination_preserves_search_and_filters(self):
        tag = Tag.objects.create(
            owner=self.user,
            name="Django",
        )
    
        for i in range(12):
            note = Note.objects.create(
                owner=self.user,
                title=f"Python tutorial {i}",
                body="Learn Django",
                note_type=Note.NoteType.TEXT,
            )
            note.tags.add(tag)

        response = self.client.get(
            reverse("home"),
            {
                "q": "Python",
                "tag": str(tag.pk),
                "type": "text",
                "archived": "false",
                "page": 2,
            },
        )
    
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].number, 2)
        self.assertEqual(response.context["search_query"], "Python")
        self.assertEqual(response.context["selected_type"], "text")
        self.assertEqual(response.context["archived_filter"], "false")

    def test_search_does_not_show_another_users_notes(self):
        other_user = User.objects.create_user(
            username="othersearchuser",
            password="test-password-123",
        )

        Note.objects.create(
            owner=other_user,
            title="Secret Python project",
            body="Private information",
        )

        response = self.client.get(
            reverse("home"),
            {"q": "Python"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Secret Python project")

    def test_pagination_links_preserve_filters(self):
        tag = Tag.objects.create(
            owner=self.user,
            name="Django",
        )

        for i in range(12):
            note = Note.objects.create(
                owner=self.user,
                title=f"Python tutorial {i}",
                body="Learn Django",
                note_type=Note.NoteType.TEXT,
            )
            note.tags.add(tag)

        response = self.client.get(
            reverse("home"),
            {
                "q": "Python",
                "tag": str(tag.pk),
                "type": "text",
                "archived": "false",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "page=2")
        self.assertContains(response, "q=Python")
        self.assertContains(response, f"tag={tag.pk}")
        self.assertContains(response, "type=text")
        self.assertContains(response, "archived=false")


class NoteFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="formtester",
            password="test-password-123",
        )

    def test_link_note_requires_url(self):
        from .forms import NoteForm

        form = NoteForm(
            data = {
                    "title": "Django documentation",
                    "body": "Official guide to Django",
                    "note_type": "link",
                    "code_language": "",
                    "url": "",
                    "archived": False,
                    "tags": [],
                },
                user = self.user,
            )

        self.assertFalse(form.is_valid())
        self.assertIn("url", form.errors)

    def test_link_note_accepts_valid_url(self):
        from .forms import NoteForm

        form = NoteForm(
            data={
                "title": "Django documentation",
                "body": "Official guide to Django",
                "note_type": "link",
                "code_language": "",
                "url": "https://docs.djangoproject.com/",
                "archived": False,
                "tags": [],
            },
            user=self.user,
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_code_note_does_not_require_url(self):
        from .forms import NoteForm

        form = NoteForm(
            data={
                "title": "Python example",
                "body": "print('Hello, world!')",
                "note_type": "code",
                "code_language": "Python",
                "url": "",
                "archived": False,
                "tags": [],
            },
            user=self.user,
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(
            form.cleaned_data["code_language"],
            "Python",
        )