import os
import time


def export_vars(request):
    return {
        "VERSION_NUMBER": os.environ["VERSION_NUMBER"]
        if "VERSION_NUMBER" in os.environ
        else str(int(time.time())),
        "COMMIT_ID": os.environ.get("COMMIT_ID"),
    }
