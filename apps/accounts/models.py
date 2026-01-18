from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from common.models import TimeStampedModel, SoftDeleteModel
from django.utils.translation import gettext_lazy as _
from .managers import UserManager

# Create your models here.

class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel, SoftDeleteModel):
    """
    Custom User model where email is the unique identifier for authentication
    instead of a username.
    """
    # --- core authentication fields ---
    email = models.EmailField(unique=True, db_index=True,
     error_messages={"unique": _("A user with that email address already exists."),})
    
    # --- Profile & Role fields ---
    role = models.CharField(max_length=50, choices=[
        ('admin', _('Administrator')),
        ('staff', _('Staff Member')),
    ], default='staff')
    # --- Permissions fields ---
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [] # Email & Password are required by default.
    def __str__(self):
        return self.email
    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    @property
    def is_admin(self):
        """Check if the user has an admin role."""
        return self.role == 'admin'
    