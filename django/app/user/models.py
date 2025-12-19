from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    PERMISSION_CHOICES = [
        ('admin', '管理者'),
        ('staff', 'スタッフ'),
    ]

    email = models.EmailField(unique=True)
    permission = models.CharField(max_length=20, choices=PERMISSION_CHOICES, default='staff', verbose_name='権限')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        verbose_name = 'ユーザー'
        verbose_name_plural = 'ユーザー'

    def __str__(self):
        return self.email