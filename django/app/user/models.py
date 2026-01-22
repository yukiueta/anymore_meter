from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """メーター管理システムユーザー"""
    PERMISSION_CHOICES = [
        ('admin', '管理者'),      # OEJP社員 - 全操作可
        ('operator', 'オペレーター'),  # 外部委託 - 閲覧と一部操作
    ]

    email = models.EmailField(unique=True)
    permission = models.CharField(max_length=20, choices=PERMISSION_CHOICES, default='operator', verbose_name='権限')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        verbose_name = 'ユーザー'
        verbose_name_plural = 'ユーザー'

    def __str__(self):
        return self.email

    @property
    def is_admin(self):
        return self.permission == 'admin'

    @property
    def is_operator(self):
        return self.permission == 'operator'