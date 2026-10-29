from django.contrib.auth import get_user_model, login
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .forms import NoteForm, RegisterForm, TagForm, NotelinkForm
from .models import Note, Tag, NoteLink, NoteRevision
from django.db.models import Q
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
from django.db.models import Prefetch

# Create your views here.

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = RegisterForm()

    return render(request, "notes/register.html", {"form":form})


@login_required
def home(request):
    notes = Note.objects.filter(
        owner=request.user
    ).order_by("-updated_at")

    tags = Tag.objects.filter(owner=request.user)
    selected_tag = request.GET.get("tag")
    search_query = request.GET.get("q", "").strip()
    selected_type = request.GET.get("type", "")
    archived_filter = request.GET.get("archived", "")

    if search_query:
        notes = notes.filter(
            Q(title__icontains=search_query) | Q(body__icontains=search_query)
        )

    if selected_tag and tags.filter(pk=selected_tag).exists():
        notes = notes.filter(tags__pk=selected_tag).distinct()

    if selected_type in Note.NoteType.values:
        notes = notes.filter(note_type=selected_type)

    if archived_filter == "true":
        notes = notes.filter(archived=True)
    elif archived_filter == "false":
        notes = notes.filter(archived=False)


    notes = notes.prefetch_related(
        Prefetch(
            "outgoing_links",
            queryset=NoteLink.objects.filter(
                source_note__owner=request.user,
                target_note__owner=request.user,
            ).select_related("target_note"),
            to_attr="visible_outgoing_links",
        ),
        Prefetch(
            "incoming_links",
            queryset=NoteLink.objects.filter(
                source_note__owner=request.user,
                target_note__owner=request.user,
            ).select_related("source_note"),
            to_attr="visible_incoming_links",
        ),
    )
    paginator = Paginator(notes, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
        
    return render(request, "notes/home.html", {"notes": notes, "tags":tags, "selected_tag":selected_tag, "search_query": search_query,"selected_type":selected_type, "note_types":Note.NoteType.choices, "archived_filter":archived_filter, "page_obj":page_obj},)

@login_required
def note_detail(request, pk):
    note = get_object_or_404(
        Note,
        pk=pk,
        owner=request.user,
    )

    outgoing_links = NoteLink.objects.filter(
        source_note=note,
        target_note__owner=request.user,
    ).select_related("target_note")

    incoming_links = NoteLink.objects.filter(
        target_note=note,
        source_note__owner=request.user,
    ).select_related("source_note")

    return render(
        request,
        "notes/note_detail.html",
        {
            "note": note,
            "outgoing_links": outgoing_links,
            "incoming_links": incoming_links,
        },
    )

@login_required
def note_revision_history(request, pk):
    note = get_object_or_404(
        Note,
        pk=pk,
        owner=request.user,
    )
    revisions = note.revisions.select_related(
        "edited_by"
    ).all()

    return render(request, "notes/note_revision_history.html", {"note":note, "revisions":revisions},)


@login_required
def note_revision_restore(request, pk, revision_id):
    if request.method != "POST":
        return redirect("note_revision_history", pk=pk)

    note = get_object_or_404(
        Note,
        pk=pk,
        owner=request.user,
    )

    revision = get_object_or_404(
        NoteRevision,
        pk=revision_id,
        note=note,
    )

    with transaction.atomic():
        # Preserve the current version before restoring.
        current_revision = NoteRevision.objects.create(
            note=note,
            title=note.title,
            body=note.body,
            note_type=note.note_type,
            code_language=note.code_language,
            url=note.url,
            archived=note.archived,
            edited_by=request.user,
        )

        # Copy current tags before changing the note's tags.
        current_revision.tags.set(note.tags.all())

        # Restore the selected revision's fields.
        note.title = revision.title
        note.body = revision.body
        note.note_type = revision.note_type
        note.code_language = revision.code_language
        note.url = revision.url
        note.archived = revision.archived
        note.save()

        # Restore the tags from the selected revision.
        note.tags.set(revision.tags.all())

    messages.success(
        request,
        "Previous version restored successfully.",
    )

    return redirect("note_revision_history", pk=note.pk)


@login_required
def note_create(request):
    if request.method == "POST":
        form = NoteForm(request.POST, user=request.user)

        if form.is_valid():
            note = form.save(commit=False)
            note.owner = request.user
            note.save()
            form.save_m2m()
            messages.success(request, "Note created successfully.")
            return redirect("home")
    else:
        form = NoteForm(user=request.user)

    return render(request, "notes/note_form.html", {"form": form})




@login_required
def note_update(request, pk):
    note = get_object_or_404(
        Note,
        pk=pk,
        owner=request.user,
    )

    if request.method == "POST":
        form = NoteForm(
            request.POST,
            instance=note,
            user=request.user,
        )

        if form.is_valid():
            if form.has_changed():
                with transaction.atomic():
                    # Get the old values from the database.
                    old_note = Note.objects.select_for_update().get(
                        pk=note.pk,
                        owner=request.user,
                    )

                    # Save the previous version.
                    revision = NoteRevision.objects.create(
                        note=old_note,
                        title=old_note.title,
                        body=old_note.body,
                        note_type=old_note.note_type,
                        code_language=old_note.code_language,
                        url=old_note.url,
                        archived=old_note.archived,
                        edited_by=request.user,
                    )

                    # Preserve the previous tags.
                    revision.tags.set(old_note.tags.all())

                    # Save the submitted changes.
                    form.save()
            else:
                form.save()

            messages.success(
                request,
                "Note updated successfully.",
            )
            return redirect("home")

    else:
        form = NoteForm(
            instance=note,
            user=request.user,
        )

    return render(
        request,
        "notes/note_form.html",
        {
            "form": form,
            "note": note,
        },
    )

@login_required
def note_delete(request, pk):
    note = get_object_or_404(
        Note,
        pk=pk,
        owner=request.user
    )

    if request.method == "POST":
        note.delete()
        messages.success(request, "Note deleted successfully.")
        return redirect("home")

    return render(
        request,
        "notes/note_confirm_delete.html",
        {"note":note}
    )

@login_required
def tag_create(request):
    if request.method == "POST":
        form = TagForm(request.POST)

        if form.is_valid():
            tag = form.save(commit=False)
            tag.owner = request.user
            tag.save()
            messages.success(request, "Tag created successfully.")
            return redirect("tag_create")
    else:
        form = TagForm()

    return render(request, "notes/tag_form.html", {"form":form})

@login_required
def note_link_create(request, pk):
    source_note = get_object_or_404(
        Note,
        pk=pk,
        owner=request.user,
    )

    if request.method == "POST":
        form = NotelinkForm(
            request.POST,
            user=request.user,
            source_note=source_note,
        )

        if form.is_valid():
            link = form.save(commit=False)
            link.source_note = source_note

            try:
                with transaction.atomic():
                    link.full_clean()
                    link.save()
            except ValidationError as error:
                if NoteLink.objects.filter(
                    source_note=source_note,
                    target_note=link.target_note,
                ).exists():
                    form.add_error(
                        "target_note",
                        "This link already exists.",
                    )
                else:
                    form.add_error(None, error)
            except IntegrityError:
                form.add_error(
                    "target_note",
                    "This link already exists.",
                )
            else:
                messages.success(
                    request,
                    "Note linked successfully.",
                )
                return redirect("home")
    else:
        form = NotelinkForm(
            user=request.user,
            source_note=source_note,
        )

    return render(
        request,
        "notes/note_link_form.html",
        {
            "form": form,
            "source_note": source_note,
        },
    )