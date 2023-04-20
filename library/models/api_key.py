import hashlib

from django.contrib.auth.models import User
from django.db import models

from booklogger import settings
from library.models.abc import TimestampedModel


class ApiKey(TimestampedModel):
    key = models.CharField(db_index=True, max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="api_keys")

    def _gen_key(self) -> str:
        self.key = hashlib.scrypt(
            self.user.password.encode("utf-8"),
            salt=settings.SECRET_KEY.encode("utf-8"),
            n=2,
            r=2,
            p=1,
        ).hex()
        self.save()
        return self.key
