from django.db import models
from django.urls import reverse

# add options if needed
CATEGORY_OPTIONS = [('io', 'I/O'), ('intro', 'Introduction')]
LEVEL_OPTIONS = [(1, 'Beginners'), (2, 'Intermediates'), (3, 'Advanced')]

# Create your models here.


class Tutorial(models.Model):

    category = models.CharField(max_length=15, choices=CATEGORY_OPTIONS, blank=True)
    title = models.CharField(max_length=255)
    html = models.TextField()
    # media = models.TextField()
    markdown = models.TextField()
    level = models.IntegerField(choices=LEVEL_OPTIONS, null=True)

    def get_absolute_url (self):
        return reverse('detail_tutorial', args=[self.id])
