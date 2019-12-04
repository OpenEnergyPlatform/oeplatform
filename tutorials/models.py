from django.db import models
from markdownx.models import MarkdownxField

# Create your models here.


class Tutorial(models.Model):
    # ToDo: Fields that are out-commented are missing according to the mockup -> datamodel ??

    # Category = models.TextField()
    title = models.TextField()
    html = models.TextField()
    markdown = MarkdownxField()
    # Level = models.IntegerField()
