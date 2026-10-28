from django import forms
from .models import Note, Tag
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

class NoteForm(forms.ModelForm):
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
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.fields["code_language"].required = False
        self.fields["code_language"].label = "programming language"
        self.fields["code_language"].help_text = ("For code notes, e.g. Python or JavaScript.")

        self.fields["url"].required = False
        self.fields["url"].label = "External URL"
        self.fields["url"].help_text = (
        "For link notes, enter a complete URL such as https://example.com."
        )

        if user is not None:
            self.fields["tags"].queryset = Tag.objects.filter(owner=user)
        else:
            self.fields["tags"].queryset = Tag.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        note_type = cleaned_data.get("note_type")
        url = cleaned_data.get("url")

        if note_type == Note.NoteType.LINK and not url:
            self.add_error(
                "url",
                "A url is required for link notes."
            )

        if note_type != Note.NoteType.LINK:
            cleaned_data["url"] = ""

        if note_type != Note.NoteType.CODE:
            cleaned_data["code_language"] = ""

        return cleaned_data

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