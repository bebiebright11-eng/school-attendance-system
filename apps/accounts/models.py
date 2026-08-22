from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model for the school attendance system.

    Extends Django's AbstractUser to add a role field that distinguishes
    between the three main actor types in the system.
    """

    class Role(models.TextChoices):
        ADMINISTRATOR = 'administrator', 'Administrator'
        TEACHER = 'teacher', 'Teacher'
        PARENT = 'parent', 'Parent/Guardian'

    # AbstractUser already provides: username, password, first_name, last_name,
    # email, is_active, is_staff, is_superuser, date_joined, last_login.
    # We override email to make it unique and add the role field.

    email = models.EmailField(
        unique=True,
        blank=False,
        help_text='Required. Used for notifications and login identification.',
    )

    role = models.CharField(
        max_length=20,
        choices=Role,
        blank=True,
        default='',
        help_text='Primary role of this user within the school system.',
    )

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        full_name = self.get_full_name()
        role_label = self.get_role_display() if self.role else 'No role'
        if full_name:
            return f'{full_name} ({role_label})'
        return f'{self.username} ({role_label})'

    @property
    def is_administrator(self):
        return self.role == self.Role.ADMINISTRATOR

    @property
    def is_teacher(self):
        return self.role == self.Role.TEACHER

    @property
    def is_parent(self):
        return self.role == self.Role.PARENT
