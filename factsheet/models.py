from django.db import models

class Factsheet(models.Model):
    id = models.UUIDField(primary_key=True)
    acronym = models.CharField(default="Factsheet's acronym", max_length=100)
    factsheetData = models.JSONField(default=dict)
