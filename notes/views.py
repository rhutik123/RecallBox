from django.contrib.auth import get_user_model, login
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .forms import NoteForm, RegisterForm, TagForm
from .models import Note

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

    return render(request, "notes/home.html", {"notes": notes})


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

    if request.method == 'POST':
        form = NoteForm(request.POST, instance=note, user=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, "Note updated successfully.")
            return redirect("home")
    else:
        form = NoteForm(instance=note, user=request.user)

    return render(
        request,
        "notes/note_form.html",
        {
            "form":form,
            "note":note
        }
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

