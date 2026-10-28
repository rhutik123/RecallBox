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