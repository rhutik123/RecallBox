from django.conf import settings
from django.db import models

# Create your models here.

class Note(models.Model):
    class NoteType(models.TextChoices):
        TEXT = "text", "Text",
        CODE = "code", "Code",
        LINK = "link", "Link"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notes"
    )

    title = models.CharField(max_length=200)
    body = models.TextField()

    code_language = models.CharField(
        max_length=50,
        blank=True
    )

    url = models.URLField(
        max_length=2048,
        blank=True
    )

    note_type = models.CharField(
        max_length=10,
        choices=NoteType.choices,
        default=NoteType.TEXT
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    archived = models.BooleanField(default=False)

    tags = models.ManyToManyField(
        "tag",
        blank=True,
        related_name="notes"
    )

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title

class Tag(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tags",
    )

    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "name"],
                name="unique_tag_name_per_owner",
        )
    ]

    def __str__(self):
        return self.name


class NoteLink(models.Model):
    source_note = models.ForeignKey(
        Note,
        on_delete=models.CASCADE,
        related_name="outgoing_links",
    )

    target_note = models.ForeignKey(
        Note,
        on_delete=models.CASCADE,
        related_name="incoming_links",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["source_note", "target_note"],
                name="unique_directional_note_link",
            ),
            models.CheckConstraint(
                condition=~models.Q(source_note=models.F("target_note")),
                name="prevent_note_self_link",
            ),
        ]

    def __str__(self):
        return f"{self.source_note} → {self.target_note}"

    def clean(self):
        super().clean()

        if self.source_note_id and self.target_note_id:
            if self.source_note.owner_id != self.target_note.owner_id:
                from django.core.exceptions import ValidationError

                raise ValidationError(
                    "You can only link notes owned by the same user."
                )