from django.db import models


class Stage(models.IntegerChoices):
    SETUP = 1
    WORKFLOW = 2
    UPLOAD = 3


class State(models.IntegerChoices):
    START = 1
    SUCCESS = 2
    FAIL = 3


