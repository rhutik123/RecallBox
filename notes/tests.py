from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Note, Tag, NoteLink, NoteRevision

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
        response = self.client.get(
            reverse("home"),
            {"q": "Django guide"},
        )

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

    
    def test_text_note_does_not_keep_url(self):
        from .forms import NoteForm

        form = NoteForm(
            data={
                "title": "My text note",
                "body": "Some useful information",
                "note_type": "text",
                "code_language": "",
                "url": "https://example.com/",
                "archived": False,
                "tags": [],
            },
            user=self.user,
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["url"], "")


    def test_text_note_does_not_keep_code_language(self):
        from .forms import NoteForm

        form = NoteForm(
            data={
                "title": "My text note",
                "body": "Some useful information",
                "note_type": "text",
                "code_language": "Python",
                "url": "",
                "archived": False,
                "tags": [],
            },
            user=self.user,
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["code_language"], "")


class NoteLinkTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="linktester",
            password="test-password-123"
        )

        self.note_a = Note.objects.create(
            owner = self.user,
            title = "Note A",
            body = "content for note A"
        )

        self.note_b = Note.objects.create(
            owner = self.user,
            title = "Note B",
            body = "content for note B"
        )

    def test_create_directional_link(self):
        link = NoteLink.objects.create(
            source_note = self.note_a,
            target_note = self.note_b,
        )

        self.assertEqual(link.source_note, self.note_a)
        self.assertEqual(link.target_note, self.note_b)

    
    def test_cannot_link_notes_owned_by_different_users(self):
        another_user = User.objects.create_user(
            username="anotheruser",
            password="test-password-123",
        )

        another_note = Note.objects.create(
            owner=another_user,
            title="Another user's note",
            body="Private content",
        )

        link = NoteLink(
            source_note=self.note_a,
            target_note=another_note,
        )

        from django.core.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            link.full_clean()


    def test_cannot_link_note_to_itself(self):
        from django.db import IntegrityError, transaction

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                NoteLink.objects.create(
                    source_note=self.note_a,
                    target_note=self.note_a,
                )

    def test_cannot_create_duplicate_directional_link(self):
        from django.db import IntegrityError, transaction

        NoteLink.objects.create(
            source_note=self.note_a,
            target_note=self.note_b,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                NoteLink.objects.create(
                    source_note=self.note_a,
                    target_note=self.note_b,
                )

    def test_reverse_directional_links_are_allowed(self):
        NoteLink.objects.create(
            source_note=self.note_a,
            target_note=self.note_b,
        )

        reverse_link = NoteLink.objects.create(
            source_note=self.note_b,
            target_note=self.note_a,
        )

        self.assertEqual(reverse_link.source_note, self.note_b)
        self.assertEqual(reverse_link.target_note, self.note_a)

        self.assertEqual(NoteLink.objects.count(), 2)

class NoteLinkViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="linkviewuser",
            password="test-password-123",
        )
        self.other_user = User.objects.create_user(
            username="otherlinkuser",
            password="test-password-123",
        )

        self.source_note = Note.objects.create(
            owner=self.user,
            title="Source note",
            body="Source content",
        )
        self.target_note = Note.objects.create(
            owner=self.user,
            title="Target note",
            body="Target content",
        )
        self.other_note = Note.objects.create(
            owner=self.other_user,
            title="Another user's note",
            body="Private content",
        )

        self.client.login(
            username="linkviewuser",
            password="test-password-123",
        )

    def test_user_can_create_link_between_own_notes(self):
        response = self.client.post(
            reverse(
                "note_link_create",
                args=[self.source_note.pk],
            ),
            {
                "target_note": self.target_note.pk,
            },
        )

        self.assertRedirects(response, reverse("home"))

        self.assertTrue(
            NoteLink.objects.filter(
                source_note=self.source_note,
                target_note=self.target_note,
            ).exists()
        )

    def test_user_cannot_link_from_another_users_note(self):
        response = self.client.post(
            reverse(
                "note_link_create",
                args=[self.other_note.pk],
            ),
            {
                "target_note": self.target_note.pk,
            },
        )

        self.assertEqual(response.status_code, 404)

        self.assertEqual(NoteLink.objects.count(), 0)

    def test_user_cannot_link_to_another_users_note(self):
        response = self.client.post(
            reverse(
                "note_link_create",
                args=[self.source_note.pk],
            ),
            {
                "target_note": self.other_note.pk,
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(
            NoteLink.objects.filter(
                source_note=self.source_note,
                target_note=self.other_note,
            ).exists()
        )

    def test_duplicate_link_shows_form_error(self):
        NoteLink.objects.create(
            source_note=self.source_note,
            target_note=self.target_note,
        )

        response = self.client.post(
            reverse(
                "note_link_create",
                args=[self.source_note.pk],
            ),
            {
                "target_note": self.target_note.pk,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            "target_note",
            "This link already exists.",
        )

        self.assertEqual(NoteLink.objects.count(), 1)    

    def test_unauthenticated_user_cannot_create_link(self):
        self.client.logout()

        response = self.client.post(
            reverse(
                "note_link_create",
                args=[self.source_note.pk],
            ),
            {
                "target_note": self.target_note.pk,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

        self.assertEqual(NoteLink.objects.count(), 0)


class NoteRevisionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="revisionuser",
            password="test-password-123",
        )
        self.other_user = User.objects.create_user(
            username="otherrevisionuser",
            password="test-password-123",
        )

        self.note = Note.objects.create(
            owner=self.user,
            title="Original title",
            body="Original body",
            note_type=Note.NoteType.TEXT,
        )

        self.client.login(
            username="revisionuser",
            password="test-password-123",
        )

    def test_meaningful_edit_saves_previous_version(self):
        response = self.client.post(
            reverse("note_update", args=[self.note.pk]),
            {
                "title": "Updated title",
                "body": "Updated body",
                "note_type": "text",
                "code_language": "",
                "url": "",
                "archived": False,
                "tags": [],
            },
        )

        self.assertRedirects(response, reverse("home"))

        self.note.refresh_from_db()

        self.assertEqual(self.note.title, "Updated title")
        self.assertEqual(self.note.body, "Updated body")

        revision = NoteRevision.objects.get(note=self.note)

        print("Revision title:", revision.title)
        print("Current title:", self.note.title)

        self.assertEqual(revision.title, "Original title")
        self.assertEqual(revision.body, "Original body")
        self.assertEqual(revision.note_type, "text")
        self.assertEqual(revision.edited_by, self.user)

    def test_unchanged_edit_does_not_create_revision(self):
        response = self.client.post(
            reverse("note_update", args=[self.note.pk]),
            {
                "title": "Original title",
                "body": "Original body",
                "note_type": "text",
                "code_language": "",
                "url": "",
                "archived": False,
                "tags": [],
            },
        )

        self.assertRedirects(response, reverse("home"))
        self.assertEqual(NoteRevision.objects.count(), 0)

    def test_user_cannot_view_another_users_revision_history(self):
        response = self.client.get(
            reverse(
                "note_revision_history",
                args=[self.note.pk],
            )
        )

        # The logged-in user owns this note, so access is allowed.
        self.assertEqual(response.status_code, 200)

        other_note = Note.objects.create(
            owner=self.other_user,
            title="Private note",
            body="Private content",
        )

        response = self.client.get(
            reverse(
                "note_revision_history",
                args=[other_note.pk],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_restore_preserves_current_version(self):
        old_revision = NoteRevision.objects.create(
            note=self.note,
            title="Older title",
            body="Older body",
            note_type=Note.NoteType.TEXT,
            edited_by=self.user,
        )

        # The note currently contains a newer version.
        self.note.title = "Current title"
        self.note.body = "Current body"
        self.note.save()

        response = self.client.post(
            reverse(
                "note_revision_restore",
                args=[self.note.pk, old_revision.pk],
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "note_revision_history",
                args=[self.note.pk],
            ),
        )

        self.note.refresh_from_db()

        # The selected older version becomes current.
        self.assertEqual(self.note.title, "Older title")
        self.assertEqual(self.note.body, "Older body")

        # The version that was current is preserved.
        self.assertTrue(
            NoteRevision.objects.filter(
                note=self.note,
                title="Current title",
                body="Current body",
            ).exists()
        )

    def test_invalid_edit_does_not_create_revision(self):
        response = self.client.post(
            reverse("note_update", args=[self.note.pk]),
            {
                "title": "Invalid change",
                "body": "Some content",
                "note_type": "link",
                "code_language": "",
                "url": "",
                "archived": False,
                "tags": [],
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(NoteRevision.objects.count(), 0)

        self.note.refresh_from_db()
        self.assertEqual(self.note.title, "Original title")

    
def test_user_cannot_restore_another_users_revision(self):
    other_note = Note.objects.create(
        owner=self.other_user,
        title="Private note",
        body="Private body",
    )

    revision = NoteRevision.objects.create(
        note=other_note,
        title="Old private title",
        body="Old private body",
        note_type=Note.NoteType.TEXT,
        edited_by=self.other_user,
    )

    response = self.client.post(
        reverse(
            "note_revision_restore",
            args=[other_note.pk, revision.pk],
        )
    )

    self.assertEqual(response.status_code, 404)

    other_note.refresh_from_db()
    self.assertEqual(other_note.title, "Private note")
    self.assertEqual(other_note.body, "Private body")
