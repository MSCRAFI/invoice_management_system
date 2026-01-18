from django.contrib import admin
from django.contrib.auth.admin import BaseUserAdmin
from .models import User
from django.utils.translation import gettext_lazy as _

# Register your models here.


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for the custom User model."""
    # The fieldsets to used in the "change user" page.
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('role',)}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    # The fieldsets to use in the "add user" page.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'password2'),
        }),
    )
    list_display = ('email', 'role', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('email',)
    ordering = ('email',)

    # The 'username' field is not in our model, so we remove it.
    # We use 'email' as the unique identifier.
    add_form_template = 'admin/auth/user/add_form.html'
    
    # Remove 'username' from the list of fields to search and display
    # as it doesn't exist on our custom model.
    # BaseUserAdmin already handles this correctly if USERNAME_FIELD is set.