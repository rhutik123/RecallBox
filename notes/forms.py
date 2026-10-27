from django import forms
from .models import Note, Tag
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ["title", "body", "note_type", "archived", "tags"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if user is not None:
            self.fields["tags"].queryset = Tag.objects.filter(owner=user)
        else:
            self.fields["tags"].queryset = Tag.objects.none()


class RegisterForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ["username"]

class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ["name"]