import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from library.models import Author, Book


@login_required
def import_book(request, query=None):
    if request.method == "GET" and not query:
        query = request.GET.get("query")

    if request.method == "POST":
        data = json.loads(request.POST["data"])
        query = request.POST.get("query")
        book = Book.objects.create_from_goodreads(data=data, query=query)
        return redirect("library:book_edit", slug=book.slug)
    else:
        goodreads_results = None
        matches = {}
        if query:
            goodreads_results = Book.objects.find_on_goodreads(query)

            for result in goodreads_results:
                match = Book.objects.search(
                    f"{result['best_book']['author']['name']} {result['best_book']['title']}"
                ).first()
                if match:
                    matches[result["id"]["#text"]] = match

        return render(
            request,
            "import.html",
            {
                "query": query,
                "goodreads_results": goodreads_results,
                "matches": matches,
            },
        )


@login_required
def bulk_import(request):
    if request.POST:
        data = request.POST["data"]

        results = []

        for entry in data.strip("\r\n").split("\n"):
            title, *author_names = entry.strip("\r\n").split(";")

            book, book_created = Book.objects.get_or_create(title__iexact=title.strip())
            if book_created:
                book.title = title.strip()

            first_author_name = author_names.pop(0).strip()
            first_author_role = ""
            if ":" in first_author_name:
                first_author_name, first_author_role = first_author_name.split(":", 1)

            (first_author, fa_created,) = Author.objects.get_or_create_by_single_name(
                first_author_name
            )
            book.first_author = first_author
            book.first_author_role = first_author_role
            book.save()

            results.append((first_author, fa_created))

            for order, name in enumerate(author_names, start=1):
                role = ""
                if ":" in name:
                    name, role = name.split(":", 1)

                author, created = Author.objects.get_or_create_by_single_name(
                    name.strip()
                )
                if author not in book.additional_authors.all():
                    book.add_author(author, order=order, role=role)

                results.append((author, created))

            results.append((book, book_created))

        return render(
            request,
            "bulk_import.html",
            {"page_title": "Import", "data": data, "results": results},
        )
    else:
        return render(request, "bulk_import.html", {"page_title": "Import"},)
