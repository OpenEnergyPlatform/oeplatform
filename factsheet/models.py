from django.db import models

class Factsheet(models.Model):
    factsheetData = models.JSONField(default=dict)
