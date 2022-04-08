import django
django.setup()
from login.models import myuser
u = myuser.objects.create_devuser('test','test@mail.com')
u.set_password('pass')
u.save()