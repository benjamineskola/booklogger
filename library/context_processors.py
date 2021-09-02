import os
import time
from typing import Any, Dict


def export_vars(request: Any) -> Dict[str, str]:
    return {
        "VERSION_NUMBER": os.environ.get("VERSION_NUMBER", str(int(time.time()))),
        "COMMIT_ID": os.environ.get("COMMIT_ID", "0000000"),
    }
