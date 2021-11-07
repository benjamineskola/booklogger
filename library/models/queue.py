#!/usr/bin/env python

from django.db import models

from library.models.abc import TimestampedModel


class Queue(TimestampedModel):
    data = models.JSONField()
