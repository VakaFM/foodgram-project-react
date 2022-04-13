from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    # username = models.CharField(max_length=150, unique=True)
    # first_name = models.CharField(max_length=150)
    # last_name = models.CharField(max_length=150)
    # password = models.CharField(max_length=150)
