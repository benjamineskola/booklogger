from django.apps import AppConfig


class LibraryConfig(AppConfig):
    name = "library"

    def ready(self) -> None:
        import library.signals  # noqa: F401
