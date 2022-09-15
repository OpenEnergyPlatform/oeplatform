from django.db import models

class FundingSourceModel(models.Model):
    name = models.CharField(max_length=100)
    uri = models.URLField(max_length=400)

class FactsheetModel(models.Model):
    name = models.CharField(max_length=100)
    uri = models.URLField(max_length=400)
    funding_source = models.ForeignKey(FundingSourceModel, on_delete = models.CASCADE)
