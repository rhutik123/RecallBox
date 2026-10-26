from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages

from .forms import NoteForm
from .models import Note

# Create your views here.

def home(request):
    notes = Note.objects.order_by("-updated_at")

    context = {
        "notes":notes
    }

    return render(request, "notes/home.html", context)

def note_create(request):
    User = get_user_model()
    demo_user = User.objects.get(username="demo_user")

    if request.method == "POST":
        form = NoteForm(request.POST)

        if form.is_valid():
            note = form.save(commit=False)
            note.owner = demo_user
            note.save()
            return redirect("home")
    else:
        form = NoteForm()

    return render(request, "notes/note_form.html", {"form": form})

def note_update(request, pk):
    User = get_user_model()
    demo_user = User.objects.get(username="demo_user")

    note = get_object_or_404(
        Note,
        pk=pk,
        owner=demo_user,
    )

    if request.method == 'POST':
        form = NoteForm(request.POST, instance=note)

        if form.is_valid():
            form.save()
            return redirect("home")
    else:
        form = NoteForm(instance=note)

    return render(
        request,
        "notes/note_form.html",
        {
            "form":form,
            "note":note
        }
    )

def note_delete(request, pk):
    User = get_user_model()
    demo_user = User.objects.get(username="demo_user")

    note = get_object_or_404(
        Note,
        pk=pk,
        owner=demo_user
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