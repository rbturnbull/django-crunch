from django.db import models

Stage = models.IntegerChoices('Stage', 'SETUP WORKFLOW UPLOAD')
State = models.IntegerChoices('State', 'START SUCCESS FAIL')
