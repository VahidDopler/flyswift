import time
import uuid
from datetime import date, timedelta

import shortuuid
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.template.backends import django
from django.utils import timezone
from django.utils.text import slugify
# from PIL import Image
from shortuuid.django_fields import ShortUUIDField
from .countries import countries

formatted_countries = [(country["code"], country["name"]) for country in countries]
Gender = (
    ("male", "Male"),
    ("female", "female")
)

level = (
    ("agency", "Agency"),
    ("normal", "Normal")
)


def user_directory_path(instance, filename):
    ext = filename.split(".")[-1]
    filename = "%s.%s" % (instance.user.id, ext),
    return f"user_{instance.user.id}/{filename}"


class MyUserModel(AbstractUser):
    full_name = models.CharField(max_length=200, default="")
    username = models.CharField(max_length=100, default="")
    email = models.EmailField(unique=True, default="")
    phone = models.CharField(max_length=200, default="")
    gender = models.CharField(max_length=100, choices=Gender)
    role = models.CharField(max_length=10, default="normal", choices=level)
    charge = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(999999999)])
    pid = ShortUUIDField(length=7, max_length=22,
                         alphabet='abcdefghijklmnopqrstuvwxyz')

    # cover_image = models.ImageField(upload_to=user_directory_path,
    #                                 default="cover.jpg", blank=True)
    country = models.CharField(max_length=200, choices=formatted_countries, blank=True, default='')
    address = models.CharField(max_length=200, null=True, blank=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username


class User_api_token(models.Model):
    user_token = ShortUUIDField(length=20, alphabet="abcdefghijklmnopqrstuvwxyz-", null=True, blank=True)
    creation_date = models.DateField(default=timezone.now, null=True, blank=True)
    due_date = models.DateField(default=date.today() + timedelta(days=30), null=True, blank=True)
    user = models.ForeignKey(MyUserModel, on_delete=models.DO_NOTHING, null=True, blank=True)

    def get_user_token(self):
        return self.user_token

    def __str__(self):
        return f'{self.user} : {self.user_token}'

    def get_creation_date(self):
        return self.creation_date
