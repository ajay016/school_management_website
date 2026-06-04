from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.conf import settings

class UserManager(BaseUserManager):
    # CHANGED: 'email' is now the required first argument. 'phone_number' is optional.
    def create_user(self, email, phone_number=None, username=None, password=None, user_type=4, **extra_fields):
        
        if not email:
            raise ValueError('The Email field must be set')
            
        email = self.normalize_email(email)
        extra_fields['user_type'] = user_type
        
        # CHANGED: Fallback username generation now uses the email prefix
        username = extra_fields.get('username')
        if not username:
            base_username = email.split('@')[0]
            username = base_username
            original_username = username
            counter = 1
            while self.model.objects.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1
            extra_fields['username'] = username

        user = self.model(email=email, phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    # CHANGED: Superuser creation now expects email
    def create_superuser(self, email, phone_number=None, username=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 0) # Root Admin

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(
            email=email,
            phone_number=phone_number,
            username=username,
            password=password,
            **extra_fields
        )


class User(AbstractBaseUser, PermissionsMixin):
    USER_TYPE_CHOICES = (
        (0, 'Root Admin'),
        (1, 'Admin'),
        (2, 'Staff'),
        (3, 'Faculty'),
        (4, 'Student'),
    )

    STATUS_CHOICES = (
        (0, 'Inactive'),
        (1, 'Active'),
        (2, 'Suspended'),
    )

    # --- Core Identity ---
    user_id = models.CharField(unique=True, max_length=20, blank=True, null=True, help_text="Student ID, Faculty ID, or Staff ID")
    username = models.CharField(unique=True, max_length=150, blank=True, null=True)
    
    # CHANGED: Email is now strictly required (no blank=True, null=True)
    email = models.EmailField(unique=True, max_length=100)
    
    # CHANGED: Phone number is now optional
    phone_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    
    # --- State Flags ---
    user_type = models.IntegerField(choices=USER_TYPE_CHOICES, default=4)
    user_status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    # --- Permissions ---
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='school_users_groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_query_name='school_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='school_users_permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_query_name='school_user',
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    # CHANGED: Authentication now uses email
    USERNAME_FIELD = 'email'
    
    # CHANGED: Removed email from here (since it's the USERNAME_FIELD) and phone is optional.
    REQUIRED_FIELDS = []

    def __str__(self):
        # Prefer email for standard string representation
        return self.email or self.username or f"User {self.pk}"
    
    def get_display_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.username or self.email
    
    
class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    
    # --- Demographics & Health ---
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    blood_group = models.CharField(max_length=5, blank=True, null=True)
    
    # --- Contact & Address ---
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    
    # --- Emergency Contact ---
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True, null=True)
    
    # --- Academic/Employment Info ---
    enrollment_date = models.DateField(null=True, blank=True, help_text="For Students")
    hire_date = models.DateField(null=True, blank=True, help_text="For Faculty/Staff")
    department = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., Science Dept, or High School")
    designation = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., Senior Teacher, 10th Grade Student")
    
    # --- Media & Extras ---
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    linkedin_profile = models.URLField(blank=True, null=True)
    biography = models.TextField(blank=True, null=True)
    timezone = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.user.get_display_name()}'s Profile"