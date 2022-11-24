from django.db import models

# Create your models here.


# Added a model to get a id (pk attribute) on each image.
# Could be added to tutorials later like:
# Tutorial[id, ..., image_id],
# delete tutorial -> if image not in other tutorial: delete image)
class UploadedImages(models.Model):
    image = models.ImageField(upload_to="image/%Y/%m/")
