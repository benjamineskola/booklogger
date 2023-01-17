import pytest


@pytest.mark.django_db()
class TestBookWithEditions:
    def test_create_new_edition(self, book_factory):
        book = book_factory(
            first_published=1900, edition_published=2000, edition_format=1
        )
        edition = book.create_new_edition(edition_format=2)

        assert edition.display_title == book.display_title
        assert edition.first_author == book.first_author
        assert edition.edition_format != book.edition_format
        assert edition.edition_published != book.edition_published
        assert edition in book.editions.all()

    def test_save_other_editions(self, book_factory, author):
        book1 = book_factory(edition_format=1)
        book1.add_author(author)
        book2 = book1.create_new_edition(edition_format=2)

        book1.series = "Foo"
        book1.rating = 5
        book1.save()
        book2.refresh_from_db()
        assert book2.series == book1.series
        assert book2.rating == book1.rating
        assert author in book2.additional_authors.all()

    def test_disambiguate_translated_editions(self, book_factory):
        book1 = book_factory(language="fr", edition_format=1)
        book2 = book1.create_new_edition(edition_format=1)

        book2.edition_language = "en"
        book2.save()
        book1.refresh_from_db()

        assert "French" in book1.get_edition_disambiguator()
        assert "English" in book2.get_edition_disambiguator()
