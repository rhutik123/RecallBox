from django import forms
from .models import Note, Tag, NoteLink
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model


class NoteForm(forms.ModelForm):
    new_tags = forms.CharField(
        required=False,
        label="Create new tags",
        help_text="Enter tags separated by commas, e.g. Django, Backend, ORM.",
        widget=forms.TextInput(attrs={
            "placeholder": "Django, Backend, ORM",
            "class": "form-control",
        }),
    )

    class Meta:
        model = Note
        fields = [
            "title",
            "body",
            "note_type",
            "code_language",
            "url",
            "archived",
            "tags",
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.fields["code_language"].required = False
        self.fields["code_language"].label = "Programming language"
        self.fields["code_language"].help_text = (
            "For code notes, e.g. Python or JavaScript."
        )

        self.fields["url"].required = False
        self.fields["url"].label = "External URL"
        self.fields["url"].help_text = (
            "For link notes, enter a complete URL such as https://example.com."
        )

        if self.user is not None:
            self.fields["tags"].queryset = Tag.objects.filter(owner=self.user)
        else:
            self.fields["tags"].queryset = Tag.objects.none()

    def clean(self):
        cleaned_data = super().clean()

        note_type = cleaned_data.get("note_type")
        url = cleaned_data.get("url")

        if note_type == Note.NoteType.LINK and not url:
            self.add_error("url", "A URL is required for link notes.")

        if note_type != Note.NoteType.LINK:
            cleaned_data["url"] = ""

        if note_type != Note.NoteType.CODE:
            cleaned_data["code_language"] = ""

        return cleaned_data

    
    def save(self, commit=True):
        note = super().save(commit=commit)

        if commit and self.user is not None:
            self.save_new_tags(note)

        return note


    def save_new_tags(self, note):
        if self.user is None:
            return

        entered_tags = self.cleaned_data.get("new_tags", "")

        tag_names = {
            name.strip()
            for name in entered_tags.split(",")
            if name.strip()
        }

        for name in tag_names:
            tag = Tag.objects.filter(
                owner=self.user,
                name__iexact=name,
            ).first()

            if tag is None:
                tag = Tag.objects.create(
                    owner=self.user,
                    name=name,
                )

            note.tags.add(tag)


class RegisterForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ["username"]

class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ["name"]

    def clean_name(self):
        name = self.cleaned_data["name"]
        return name.strip()

class NotelinkForm(forms.ModelForm):
    class Meta:
        model = NoteLink
        fields = ["target_note"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        source_note = kwargs.pop("source_note", None)
        super().__init__(*args, **kwargs)

        if user is not None:
            self.fields["target_note"].queryset = Note.objects.filter(
                owner=user
            )
        else:
            self.fields["target_note"].queryset = Note.objects.none()

        if source_note is not None:
            self.fields["target_note"].queryset = (
                self.fields["target_note"].queryset.exclude(pk=source_note.pk)
            )