from django.db import models

class Factsheet(models.Model):
    factsheetData = models.JSONField()
    factsheetDataBackup = models.JSONField()
