from django.contrib import admin
from django.contrib.auth.models import Group
from .models import User, UserProfile














# 1. Create an Inline for the UserProfile
# This allows us to edit the profile directly inside the User admin page.
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profile'
    fk_name = 'user'
    
    # Organizing the inline fields neatly
    fieldsets = (
        ('Demographics & Health', {
            'fields': ('date_of_birth', 'gender', 'blood_group')
        }),
        ('Academic / Employment Info', {
            'fields': ('enrollment_date', 'hire_date', 'department', 'designation')
        }),
        ('Contact & Address', {
            'fields': ('address', 'city', 'state', 'postal_code', 'country')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone')
        }),
        ('Media & Extras', {
            'fields': ('profile_picture', 'linkedin_profile', 'biography', 'timezone'),
            'classes': ('collapse',) # Hides this section by default to save space
        }),
    )

# 2. Register the Custom User Model
@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    # What columns to show in the list view
    list_display = ('phone_number', 'get_display_name', 'user_id', 'user_type', 'user_status', 'is_active')
    
    # Filters on the right sidebar
    list_filter = ('user_type', 'user_status', 'is_active', 'is_staff')
    
    # Search bar configuration (using related fields)
    search_fields = ('phone_number', 'email', 'first_name', 'last_name', 'user_id', 'username')
    
    # Default ordering (newest first)
    ordering = ('-created_at',)
    
    # Attach the profile inline here
    inlines = (UserProfileInline,)
    
    # Organizing the main User fields
    fieldsets = (
        ('Core Identity', {
            'fields': ('user_id', 'first_name', 'last_name', 'phone_number', 'email', 'username')
        }),
        ('Authentication', {
            'fields': ('password',),
            'help_text': "Note: Raw passwords saved here will be hashed automatically."
        }),
        ('State & Permissions', {
            'fields': ('user_type', 'user_status', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Timestamps', {
            'fields': ('last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'last_login')

    # Override save_model to ensure passwords get hashed if an admin creates/updates a user manually in the panel
    def save_model(self, request, obj, form, change):
        if obj.pk:
            # If updating an existing user, check if password changed
            orig_obj = User.objects.get(pk=obj.pk)
            if obj.password != orig_obj.password:
                obj.set_password(obj.password)
        else:
            # If creating a new user, hash the password
            obj.set_password(obj.password)
        super().save_model(request, obj, form, change)


# 3. Optional: Register UserProfile independently 
# Useful if admins want to search specifically by department, designation, or blood group without going through the User table.
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'designation', 'blood_group', 'city')
    list_filter = ('blood_group', 'gender', 'department')
    search_fields = ('user__phone_number', 'user__first_name', 'user__last_name', 'department', 'designation')
    
    # We can use the same fieldsets as the inline for consistency
    fieldsets = UserProfileInline.fieldsets

# (Optional) Unregister the default Group model if you don't plan on using Django's default groups
# admin.site.unregister(Group)