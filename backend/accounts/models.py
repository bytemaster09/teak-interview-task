from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        AUTHOR = "author", "Author"
        READER = "reader", "Reader"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.READER)
    bio = models.TextField(blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["role"]),
        ]

    @property
    def is_author(self):
        return self.role == self.Role.AUTHOR

    def __str__(self):
        return self.email
