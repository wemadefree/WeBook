from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
import webook.users.media_pathing as media_path
from webook.arrangement.models import Person
from autoslug import AutoSlugField


class CustomUserManager(BaseUserManager):
    """
    Custom user model manager without a username field.
    """

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

class User(AbstractUser):
    username = None
    email = models.EmailField(_('email address'), unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    person = models.ForeignKey(Person, blank=True, null=True, on_delete=models.RESTRICT)
    slug = AutoSlugField(populate_from="_get_slug", blank=True, unique=True)

    objects = CustomUserManager()

    profile_picture = models.ImageField(
        name="profile_picture",
        verbose_name=_("Profile Picture"),
        upload_to=media_path.profile_picture_path,
        blank=True,
    )

    def get_absolute_url(self):
        return reverse(
            "users:detail", kwargs={"slug": self.slug}
        )

    @property 
    def get_representative_name (self) -> str:
        """ Get a 'friendly' representative name which can be used in frontend """
        return self._get_slug

    @property
    def _get_slug (self):
        """
            Generate slug for this user. We want to, as far as it is possible, generate the slug based on the person associated with this user. 
            But if no person is available we will settle for the first fragment of the users email address.
            If one later attaches a person, one should set slug field to None, and it will regenerate the slug based
            on this method, thus the slug should be now based on the person instance.
        """
        if (self.person is None or self.person.first_name == "" and self.person.last_name == ""):
            return str(self.email).split('@')[0]
        return str(self.person)
        

    def __str__(self) -> str:
        return self.email
