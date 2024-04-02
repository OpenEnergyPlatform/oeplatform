import os    
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oeplatform.settings")
django.setup()
from login.models import myuser
u = myuser.objects.create_devuser('test','test@mail.com')
u.set_password('pass')
u.save()