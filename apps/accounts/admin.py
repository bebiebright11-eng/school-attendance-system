from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin configuration for the custom User model.

    Extends Django's built-in UserAdmin so password hashing, permission
    management, and the change-password form all work out of the box.
    We add the role field to the relevant fieldsets and list views.
    """

    # Columns shown in the user list
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('last_name', 'first_name')

    # Add role to the "Personal info" section of the change form
    fieldsets = BaseUserAdmin.fieldsets + (
        ('School System', {'fields': ('role',)}),
    )

    # Add role to the add-user form
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email')}),
        ('School System', {'fields': ('role',)}),
    )
