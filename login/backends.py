from django.contrib.auth.backends import ModelBackend
from django.db import models
from django.db.models import Q

from .models import myuser


class ModelBackendWithEmail(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        """Change authenticate of ModelBackend

        Args:
            request: not used
            username(str): username or email from login form
            password(str): user password from login form
        """
        try:
            # find user object based on name OR email
            user = myuser.objects.get(Q(name=username) | Q(email=username))
        except models.ObjectDoesNotExist:
            return None

        if user.check_password(password):
            return user
        else:
            return None
