import os


def export_vars(request):
    return {
        "VERSION_NUMBER": os.environ["VERSION_NUMBER"],
        "COMMIT_ID": os.environ.get("COMMIT_ID"),
    }
