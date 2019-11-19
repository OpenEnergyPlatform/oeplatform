from django.db import models

# Create your models here.

class Tutorial(models.Model):
    title = models.TextField()
    html = models.TextField()
    markdown = models.TextField()