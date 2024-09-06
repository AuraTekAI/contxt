
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin

class CustomAccountManager(BaseUserManager):
    """
    Custom user model manager for handling user creation with a username as the unique identifier
    instead of an email address. This class provides methods for creating users with different
    levels of access (regular users, staff users, and superusers).

    Methods:
    - _create_user(self, user_name, password, **extra_fields):
        Creates and saves a user with the given username and password.
        Parameters:
            user_name (str): The username of the user.
            password (str): The password for the user.
            **extra_fields (dict): Additional fields for the user.
        Returns:
            User: The created user instance.

    - create_staff(self, user_name, password, **extra_fields):
        Creates and saves a staff user with the given username and password.
        Parameters:
            user_name (str): The username of the staff user.
            password (str): The password for the staff user.
            **extra_fields (dict): Additional fields for the staff user.
        Returns:
            User: The created staff user instance.

    - create_superuser(self, user_name, password, **extra_fields):
        Creates and saves a superuser with the given username and password.
        Parameters:
            user_name (str): The username of the superuser.
            password (str): The password for the superuser.
            **extra_fields (dict): Additional fields for the superuser.
        Returns:
            User: The created superuser instance.

    - create_user(self, user_name, password, **extra_fields):
        Creates and saves a regular user with the given username and password.
        Parameters:
            user_name (str): The username of the user.
            password (str): The password for the user.
            **extra_fields (dict): Additional fields for the user.
        Returns:
            User: The created regular user instance.
    """

    def _create_user(self, user_name, password, **extra_fields):
        """
        Create and save a User with the given username and password.
        This method is called by `create_user`, `create_staff`, and `create_superuser` methods.
        Ensures that the username is provided and hashes the password before saving.

        Parameters:
            user_name (str): The username of the user.
            password (str): The password for the user.
            **extra_fields (dict): Additional fields for the user.

        Returns:
            User: The created user instance.

        Raises:
            ValueError: If the `user_name` is not provided.
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
        Staff users have `is_staff=True` which allows them to access the admin interface.

        Parameters:
            user_name (str): The username of the staff user.
            password (str): The password for the staff user.
            **extra_fields (dict): Additional fields for the staff user.

        Returns:
            User: The created staff user instance.
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
        Create and save a superuser with the given username and password.
        Superusers have both `is_staff=True` and `is_superuser=True`, granting full access
        to the admin interface.

        Parameters:
            user_name (str): The username of the superuser.
            password (str): The password for the superuser.
            **extra_fields (dict): Additional fields for the superuser.

        Returns:
            User: The created superuser instance.

        Raises:
            ValueError: If `is_staff` or `is_superuser` fields are not set to True.
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
        Regular users have `is_active=True` by default.

        Parameters:
            user_name (str): The username of the user.
            password (str): The password for the user.
            **extra_fields (dict): Additional fields for the user.

        Returns:
            User: The created regular user instance.
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
    """
    Custom user model with additional fields for a user profile.
    This model uses `user_name` as the unique identifier for authentication.

    Fields:
    - name (str): Full name of the user.
    - pic_number (str): Unique identifier number for the user, optional.
    - is_active (bool): Indicates whether the user account is active.
    - user_name (str): Unique username for the user.
    - age (int): Age of the user, optional.
    - sex (str): Gender of the user, optional.
    - private_mode (bool): Indicates if the user has private mode enabled.
    - account_balance (Decimal): Balance of the user's account.
    - custom_email (EmailField): Optional custom email address for the user.
    - active_until_date (DateField): Date until which the user's account is active, optional.
    - sms_left (Decimal): Number of SMS left for the user, optional.
    - custom_name (str): Optional custom name for the user.
    - extra_sms (Decimal): Extra SMS quota for the user.

    - is_staff (bool): Indicates if the user has staff privileges.
    - is_superuser (bool): Indicates if the user has superuser privileges.
    - updated_at (DateTimeField): Timestamp of the last update to the user's account.
    - created_at (DateTimeField): Timestamp of the user's account creation.

    Manager:
    - objects (CustomAccountManager): Custom manager for creating and managing user accounts.

    Meta:
    - db_table (str): Specifies the database table name as 'users'.
    - verbose_name (str): Human-readable name for the model.
    - verbose_name_plural (str): Human-readable plural name for the model.
    - indexes (list): List of database indexes for optimizing queries on `is_active` and `custom_email` fields.

    Methods:
    - save(self, *args, **kwargs):
        Custom save method to handle additional logic related to `extra_sms` and `sms_left`.
    - __str__(self):
        Returns a string representation of the user, which is their `name`.
    """

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
        """
        Custom save method for handling additional logic related to SMS quotas.
        Currently a placeholder for additional logic related to `extra_sms` and `sms_left`.

        Parameters:
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Calls the superclass's `save` method to perform the actual saving.
        """
        # TODO create logic for extra sms and sms left
        super().save(*args, **kwargs)

    def __str__(self):
        """
        Returns the string representation of the user.

        Returns:
            str: The user's name.
        """
        return self.name

    class Meta:
        db_table = 'users'
        verbose_name = 'users'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['custom_email']),
        ]

class BotAccount(models.Model):
    """
    Represents a bot account that interacts with Corrlinks.

    Attributes:
        bot_name (CharField): The name of the bot (e.g., 'bot1', 'bot2').
        email_address (EmailField): The email address associated with the bot.
        password (CharField): The password associated with the bot.
        last_read_message_id (CharField): The MessageID of the last read email.
        is_active (BooleanField): Indicates whether the bot is currently active.
        created_at (DateTimeField): Timestamp when the bot account was created.
        updated_at (DateTimeField): Timestamp when the bot account was last updated.
    """

    bot_name = models.CharField(max_length=50, unique=True, db_index=True)

    email_address = models.EmailField(unique=True, db_index=True)
    email_password = models.CharField(max_length=128, null=True, blank=True)
    corrlinks_password = models.CharField(max_length=128, null=True, blank=True)
    email_url = models.CharField(max_length=128, null=True, blank=True)

    last_read_message_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)

    is_active = models.BooleanField(default=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.bot_name

    class Meta:
        db_table = 'bot_accounts'
        verbose_name = 'bot_account'
        verbose_name_plural = 'bot_accounts'
        indexes = [
            models.Index(fields=['bot_name', 'is_active']),
            models.Index(fields=['email_address']),
            models.Index(fields=['last_read_message_id']),
        ]
