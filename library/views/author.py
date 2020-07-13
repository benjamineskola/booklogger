from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views import generic

from library.forms import AuthorForm
from library.models import Author


class DetailView(generic.DetailView):
    model = Author
    template_name = "authors/details.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = str(self.get_object())
        return context


class IndexView(generic.ListView):
    template_name = "authors/list.html"
    model = Author
    paginate_by = 100

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_authors"] = self.get_queryset().count()
        context["page_title"] = "Authors"
        return context


@login_required
def edit(request, slug):
    author = get_object_or_404(Author, slug=slug)
    if request.method == "POST":
        form = AuthorForm(request.POST, instance=author)
        if form.is_valid():
            author = form.save()
            return redirect("library:author_details", slug=author.slug)
        else:
            for field in form.errors:
                form[field].field.widget.attrs["class"] += " is-invalid"

            return render(
                request,
                "authors/edit_form.html",
                {"form": form, "item": author, "page_title": f"Editing {author}",},
            )
    else:
        form = AuthorForm(instance=author)

        return render(
            request,
            "authors/edit_form.html",
            {"form": form, "item": author, "page_title": f"Editing {author}",},
        )


@login_required
def new(request):
    if request.method == "POST":
        form = AuthorForm(request.POST)
        if form.is_valid():
            author = form.save()
            return redirect("library:author_details", slug=author.slug)
        else:
            for field in form.errors:
                form[field].field.widget.attrs["class"] += " is-invalid"

            return render(
                request,
                "authors/edit_form.html",
                {"form": form, "page_title": f"Editing {author}",},
            )
    else:
        form = AuthorForm()

        return render(
            request,
            "authors/edit_form.html",
            {"form": form, "page_title": "New author"},
        )
