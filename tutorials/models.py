from django.db import models
from django.urls import reverse

# add options if needed
CATEGORY_OPTIONS = [('general', 'General'),
                    ('publication', 'Publication/Licensing'), 
                    ('io', 'Upload/Download'), 
                    ('data_structure', 'Data Structure'), 
                    ('ontology', 'Ontology'), 
                    ('other', 'Other Topics')]

LEVEL_OPTIONS = [(1, 'Beginner'), (2, 'Intermediate'), (3, 'Expert')]
LANGUAGE = [('de', 'german'), ('en', 'english'), ('fr', 'french')]
LICENSE = [('none', 'No'), ('cc0', 'CC0'), ('agpl', 'AGPL')]
MEDIUM = [('video', 'video'), ('text', 'text'), ('jupyter', 'jupyter notebook')]

# Create your models here.


class Tutorial(models.Model):

    category = models.CharField(max_length=15, choices=CATEGORY_OPTIONS, blank=True)
    title = models.CharField(max_length=255)
    html = models.TextField()
    media_src = models.URLField(verbose_name='youtube video url', null=True, blank=True)
    markdown = models.TextField()
    level = models.IntegerField(choices=LEVEL_OPTIONS, null=True)
    language = models.CharField(choices=LANGUAGE, null=True, max_length=20)
    medium = models.CharField(choices=MEDIUM, null=True, max_length=20)
    license = models.CharField(choices=LICENSE, null=True, max_length=30)
    creator = models.CharField(verbose_name='creator/copyright', null=True, max_length=254)
    email_contact = models.EmailField(verbose_name='email contact', max_length=255, null=True)
    github_contact = models.CharField(verbose_name='github contact', max_length=50, blank=True)

    def get_absolute_url (self):
        return reverse('detail_tutorial', args=[self.id])
