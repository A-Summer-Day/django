from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.


class User(AbstractUser):
    is_employee = models.BooleanField(default=False)
    is_client = models.BooleanField(default=False)
    is_business_partner = models.BooleanField(default=False)
    contact_id = models.CharField(max_length=100, blank=True)
    email = models.EmailField(unique=True, max_length=100)
    username = models.CharField(
        unique=True, 
        max_length=100,
        error_messages={
            'unique': 'A user with that email already exists.'
        })

    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def __str__(self) -> str:
        return self.full_name()
