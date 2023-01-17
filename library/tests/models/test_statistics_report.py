import pytest
from django.utils import timezone

from library.models import StatisticsReport, Tag


@pytest.mark.django_db()
class TestStatisticsReport:
    @pytest.fixture(autouse=True)
    def _tags(self):
        Tag.objects.get_or_create(name="fiction")
        Tag.objects.get_or_create(name="non-fiction")

    @pytest.fixture()
    def report(self):
        r, _ = StatisticsReport.objects.get_or_create(year=timezone.now().year)
        return r

    def test_count(self, read_book_factory):
        read_book_factory()
        read_book_factory()
        report, _ = StatisticsReport.objects.get_or_create(year=timezone.now().year)

        assert report.count == 2

    def test_page_count(self, read_book_factory):
        read_book_factory(page_count=100)
        read_book_factory(page_count=100)
        report, _ = StatisticsReport.objects.get_or_create(year=timezone.now().year)

        assert report.page_count == 200

    def test_counts_empty(self, read_book_factory):  # noqa: ARG002
        report, _ = StatisticsReport.objects.get_or_create(year=timezone.now().year)
        assert not report.count
        assert not report.page_count

    def test_longest_shortest(self, read_book_factory):
        book1 = read_book_factory(page_count=100)
        book2 = read_book_factory(page_count=200)
        report, _ = StatisticsReport.objects.get_or_create(year=timezone.now().year)

        assert report.longest == book2
        assert report.shortest == book1

    def test_longest_shortest_empty(self, read_book_factory):  # noqa: ARG002
        report, _ = StatisticsReport.objects.get_or_create(year=timezone.now().year)
        assert not report.longest
        assert not report.shortest
