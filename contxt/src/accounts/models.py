
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin

class CustomAccountManager(BaseUserManager):
    """
    Custom user model manager where username is the unique identifier
    for authentication instead of email.
    """

    def _create_user(self, user_name, password, **extra_fields):
        """
        Create and save a User with the given username and password.
        """
        if not user_name:
            raise ValueError("Users must have a username!")

        user = self.model(
            user_name=user_name,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_staff(self, user_name, password, **extra_fields):
        """
        Create and save a staff User with the given username and password.
        """
        user = self._create_user(
            user_name=user_name,
            password=password,
            **extra_fields,
        )
        user.is_staff = True
        user.save(using=self._db)
        return user

    def create_superuser(self, user_name, password, **extra_fields):
        """
        Create and save a SuperUser with the given username and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        user = self._create_user(
            user_name=user_name,
            password=password,
            **extra_fields,
        )

        user.save(using=self._db)

        return user

    def create_user(self, user_name, password, **extra_fields):
        """
        Create and save a regular User with the given username and password.
        """
        extra_fields.setdefault("is_active", True)

        user = self._create_user(
            user_name=user_name,
            password=password,
            **extra_fields,
        )

        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=255)
    pic_number = models.CharField(max_length=100, unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    user_name = models.CharField(max_length=100, unique=True, null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    sex = models.CharField(max_length=10, null=True, blank=True)
    private_mode = models.BooleanField(default=False)
    account_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    custom_email = models.EmailField(max_length=100, null=True, blank=True)
    active_until_date = models.DateField(null=True, blank=True)
    sms_left = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0.0)
    custom_name = models.CharField(max_length=100, null=True, blank=True)
    extra_sms = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = CustomAccountManager()

    USERNAME_FIELD = "user_name"
    REQUIRED_FIELDS = ["name"]

    def save(self, *args, **kwargs):
        # TODO create logic for extra sms and sms left
        super().save(*args, **kwargs)

    def _str_(self):
        return self.name

    class Meta:
        db_table = 'users'
        verbose_name = 'users'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['custom_email']),
        ]
