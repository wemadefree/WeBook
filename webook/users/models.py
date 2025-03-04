from django.forms import ValidationError
import pytz
from autoslug import AutoSlugField
from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import webook.users.media_pathing as media_path
from webook.arrangement.models import Person, ServiceEmail


class LoginAudit(models.Model):
    time_stamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey("User", on_delete=models.RESTRICT, null=True)
    attempted_email = models.EmailField(null=True)

    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=255)
    successful = models.BooleanField(default=False)
    login_type = models.CharField(max_length=255, default="email")

    threshold_exceeded = models.BooleanField(default=False)


class UserTokenRevocation(models.Model):
    # All tokens that are issued before this timestamp are to be considered revoked. ( iat < revocation_timestamp )
    revocation_timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey("User", on_delete=models.RESTRICT)
    revocation_reason = models.CharField(max_length=512, null=True, blank=True)


class UserResetPasswordToken(models.Model):
    user = models.ForeignKey("User", on_delete=models.RESTRICT)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    token = models.CharField(max_length=255, unique=True)


class CustomUserManager(BaseUserManager):
    """
    Custom user model manager without a username field.
    """

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(_("email address"), unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    person = models.ForeignKey(Person, blank=True, null=True, on_delete=models.RESTRICT)
    slug = AutoSlugField(populate_from="_get_slug", blank=True, unique=True)

    TIMEZONE_CHOICES = zip(pytz.all_timezones, pytz.all_timezones)
    timezone = models.CharField(max_length=255, default=settings.USER_DEFAULT_TIMEZONE)

    is_user_admin = models.BooleanField(
        verbose_name="User Administrator", default=False
    )

    objects = CustomUserManager()

    profile_picture = models.ImageField(
        name="profile_picture",
        verbose_name=_("Profile Picture"),
        upload_to=media_path.profile_picture_path,
        blank=True,
        null=True,
    )

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"slug": self.slug})

    @property
    def is_service_coordinator(self) -> bool:
        if self.person is None:
            return False

        return ServiceEmail.objects.filter(email=self.email).exists()

    @property
    def get_representative_name(self) -> str:
        """Get a 'friendly' representative name which can be used in frontend"""
        return self._get_slug

    @property
    def role(self):
        return self.groups.first().name

    @property
    def _get_slug(self):
        """
        Generate slug for this user. We want to, as far as it is possible, generate the slug based on the person associated with this user.
        But if no person is available we will settle for the first fragment of the users email address.
        If one later attaches a person, one should set slug field to None, and it will regenerate the slug based
        on this method, thus the slug should be now based on the person instance.
        """
        if (
            self.person is None
            or self.person.first_name == ""
            and self.person.last_name == ""
        ):
            return str(self.email).split("@")[0]
        return str(self.person)

    def __str__(self) -> str:
        return self.email
