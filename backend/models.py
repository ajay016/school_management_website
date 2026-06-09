from django.db import models
import io
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions
from django.core.files.base import ContentFile
from PIL import Image, ImageOps
from django.conf import settings
from django.utils.text import slugify
from django.core.files.base import ContentFile












class HomeSlider(models.Model):
    # --- Images ---
    slider_image = models.ImageField(
        upload_to='sliders/backgrounds/', 
        blank=True, null=True,
        help_text="Optional background image (Suggested: 1920x600px). If left blank, the theme's background color will be used."
    )
    hero_image = models.ImageField(
        upload_to='sliders/heroes/', 
        help_text="Will be auto-cropped to 700x460 pixels and optimized under 500KB."
    )
    
    # --- Text Content (Updated for character limits) ---
    greeting_badge = models.CharField(max_length=30, help_text="Small badge text (Max 30 characters).")
    heading = models.CharField(max_length=50, help_text="Main slider heading (Max 50 characters).")
    short_description = models.TextField(max_length=150, help_text="Brief description (Max 150 characters).")
    
    # --- Button ---
    button_label = models.CharField(max_length=30, blank=True, null=True, help_text="Text inside the button (e.g., 'Learn More').")
    button_link = models.CharField(max_length=255, blank=True, null=True, help_text="Can be a full URL (https://...) or a relative path (/about/).")
    
    # --- Status & Timestamps ---
    is_active = models.BooleanField(default=True, help_text="Uncheck to hide this slider from the homepage.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Home Slider"
        verbose_name_plural = "Home Sliders"
        ordering = ['-created_at']

    def __str__(self):
        return self.heading

    def clean(self):
        super().clean()
        errors = {}

        # 1. Character Count Validations
        if self.greeting_badge and len(self.greeting_badge) > 30:
            errors['greeting_badge'] = "Greeting message cannot exceed 30 characters."
            
        if self.heading and len(self.heading) > 50:
            errors['heading'] = "Heading cannot exceed 50 characters."
            
        if self.short_description and len(self.short_description) > 150:
            errors['short_description'] = "Short description cannot exceed 150 characters."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Check if hero_image is present and is a newly uploaded file
        if self.hero_image and not getattr(self.hero_image, '_committed', True):
            img = Image.open(self.hero_image)
            
            # Convert to RGB to ensure compatibility
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
                
            # Auto-crop to exact dimensions keeping aspect ratio
            img = ImageOps.fit(img, (700, 460), Image.Resampling.LANCZOS)
            
            output = io.BytesIO()
            quality = 95
            img.save(output, format='JPEG', quality=quality)
            
            # Compress iteratively if file size is > 500KB
            while output.tell() > 500 * 1024 and quality > 20:
                output.seek(0)
                output.truncate()
                quality -= 5
                img.save(output, format='JPEG', quality=quality)
                
            output.seek(0)
            
            # Save the optimized image
            filename = f"{self.hero_image.name.rsplit('.', 1)[0]}.jpg"
            self.hero_image.save(filename, ContentFile(output.read()), save=False)

        super().save(*args, **kwargs)
        


PAGE_CHOICES = [
    # ('contact',           'Contact'),
    # ('faculty_junior',    'Faculty — Junior School'),
    # ('faculty_middle',    'Faculty — Middle School'),
    # ('faculty_senior',    'Faculty — Senior School'),
    # ('gallery',           'Gallery'),
    # ('events',            'Events'),
    # ('notices',           'Notices'),
    # ('students',          'Students'),
    # ('results',           'Results'),
    # ('admission_results', 'Admission Results'),
    ('layout_1',          'Layout 1 — Image with Description'),
    ('layout_2',          'Layout 2 — Photo Grid'),
    ('layout_3',          'Layout 3 — Rich Text'),
    # Dynamic model-driven dropdowns (no SubMenu needed)
    # ('facilities_list',  'Facilities — dropdown from Facility model'),
    # ('curriculum_list',  'Curriculum — dropdown from Curriculum Stages'),
]


# Maps PAGE_CHOICES keys for special pages to their named URL.
# Layout pages resolve dynamically via /page/<menu>/<submenu>/.
_SPECIAL_PAGE_URL_NAMES = {
    'events':            'events',
    'notices':           'notices',
    'contact':           'contact',
    'gallery':           'galleries',
    # faculty/students/results pages will be added when those views exist
}


class Menu(models.Model):
    name      = models.CharField(max_length=100)
    slug      = models.SlugField(unique=True, blank=True)
    order     = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    # Only set when this menu links directly to a page (no submenus)
    page      = models.CharField(max_length=30, choices=PAGE_CHOICES,
                    blank=True, null=True)

    class Meta:
        ordering = ['order']
        verbose_name = "Menu"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Return the public URL for a direct-page menu (no submenus)."""
        if not self.page:
            return '#'
        from django.urls import reverse
        if self.page in _SPECIAL_PAGE_URL_NAMES:
            return reverse(_SPECIAL_PAGE_URL_NAMES[self.page])
        if self.page in ('layout_1', 'layout_2', 'layout_3'):
            try:
                return reverse('direct_menu_page', kwargs={'menu_slug': self.slug})
            except Exception:
                return '#'
        return '#'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class SubMenu(models.Model):
    menu      = models.ForeignKey(Menu, on_delete=models.CASCADE,
                    related_name='submenus')
    name      = models.CharField(max_length=100)
    slug      = models.SlugField(blank=True)
    order     = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    page      = models.CharField(max_length=30, choices=PAGE_CHOICES)

    class Meta:
        ordering = ['menu', 'order']
        unique_together = [['menu', 'slug']]
        verbose_name = "Sub Menu"

    def __str__(self):
        return f"{self.menu.name}  ›  {self.name}"

    def get_absolute_url(self):
        """
        Return the public URL for this submenu item.
        - layout_1/2/3  → /page/<menu-slug>/<submenu-slug>/
        - special pages → their named route (events, notices, etc.)
        """
        from django.urls import reverse
        if self.page in ('layout_1', 'layout_2', 'layout_3'):
            return reverse('dynamic_page', kwargs={
                'menu_slug':    self.menu.slug,
                'submenu_slug': self.slug,
            })
        if self.page in _SPECIAL_PAGE_URL_NAMES:
            return reverse(_SPECIAL_PAGE_URL_NAMES[self.page])
        return '#'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# LAYOUT CONTENT  — only used when SubMenu.page is layout_1 / 2 / 3
# ─────────────────────────────────────────────────────────────────────────────

class PageSection(models.Model):
    """Layout 1 — image + description blocks.
    Exactly one of `submenu` or `menu` must be set (enforced at application level).
    """
    submenu     = models.ForeignKey(SubMenu, on_delete=models.CASCADE,
                      related_name='sections', null=True, blank=True)
    menu        = models.ForeignKey('Menu', on_delete=models.CASCADE,
                      related_name='page_sections', null=True, blank=True)
    image       = models.ImageField(upload_to='cms/sections/', blank=True, null=True)
    image_align = models.CharField(max_length=5,
                      choices=[('left', 'Left'), ('right', 'Right')],
                      default='left')
    person_name = models.CharField(max_length=150, blank=True, null=True)
    designation = models.CharField(max_length=150, blank=True, null=True)
    heading     = models.CharField(max_length=200, blank=True, null=True)
    body        = models.TextField()
    order       = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        if self.submenu:
            return f"{self.submenu} — block {self.order}"
        return f"{self.menu.name} (direct) — block {self.order}"


class PagePhoto(models.Model):
    """Layout 2 — photo grid.
    Exactly one of `submenu` or `menu` must be set (enforced at application level).
    """
    submenu = models.ForeignKey(SubMenu, on_delete=models.CASCADE,
                  related_name='photos', null=True, blank=True)
    menu    = models.ForeignKey('Menu', on_delete=models.CASCADE,
                  related_name='page_photos', null=True, blank=True)
    image   = models.ImageField(upload_to='cms/photos/')
    caption = models.CharField(max_length=200, blank=True, null=True)
    order   = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        owner = self.submenu or self.menu
        return f"{owner} — photo {self.order}"

    def save(self, *args, **kwargs):
        if self.image and not getattr(self.image, '_committed', True):
            img = Image.open(self.image)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            img.thumbnail((1200, 900), Image.Resampling.LANCZOS)
            output = io.BytesIO()
            quality = 88
            img.save(output, format='JPEG', quality=quality)
            while output.tell() > 300 * 1024 and quality > 20:
                output.seek(0); output.truncate(); quality -= 5
                img.save(output, format='JPEG', quality=quality)
            output.seek(0)
            self.image.save(
                f"{self.image.name.rsplit('.', 1)[0]}.jpg",
                ContentFile(output.read()), save=False
            )
        super().save(*args, **kwargs)


class PageRichText(models.Model):
    """Layout 3 — rich text blocks (Quill / CKEditor).
    Exactly one of `submenu` or `menu` must be set (enforced at application level).
    """
    submenu       = models.ForeignKey(SubMenu, on_delete=models.CASCADE,
                        related_name='rich_texts', null=True, blank=True)
    menu          = models.ForeignKey('Menu', on_delete=models.CASCADE,
                        related_name='page_rich_texts', null=True, blank=True)
    section_title = models.CharField(max_length=200, blank=True, null=True)
    content       = models.TextField(help_text="Raw HTML from the editor")
    order         = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        if self.submenu:
            return f"{self.submenu} — block {self.order}"
        return f"{self.menu.name} (direct) — block {self.order}"


# ─────────────────────────────────────────────────────────────────────────────
# EXCEL UPLOADS
# ─────────────────────────────────────────────────────────────────────────────

class FacultyUpload(models.Model):
    LEVEL_CHOICES = [
        ('junior', 'Junior School'),
        ('middle', 'Middle School'),
        ('senior', 'Senior School'),
    ]
    label        = models.CharField(max_length=200)
    school_level = models.CharField(max_length=10, choices=LEVEL_CHOICES)
    file         = models.FileField(upload_to='uploads/faculty/')
    is_active    = models.BooleanField(default=True)
    uploaded_by  = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                       on_delete=models.SET_NULL, related_name='+')
    uploaded_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Faculty Upload"

    def __str__(self):
        return f"{self.label} ({self.get_school_level_display()})"


class StudentUpload(models.Model):
    label       = models.CharField(max_length=200)
    file        = models.FileField(upload_to='uploads/students/')
    is_active   = models.BooleanField(default=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                      on_delete=models.SET_NULL, related_name='+')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Student Upload"

    def __str__(self):
        return self.label


class ResultUpload(models.Model):
    label       = models.CharField(max_length=200)
    file        = models.FileField(upload_to='uploads/results/')
    is_active   = models.BooleanField(default=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                      on_delete=models.SET_NULL, related_name='+')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Result Upload"

    def __str__(self):
        return self.label


class AdmissionResultUpload(models.Model):
    label        = models.CharField(max_length=200)
    grade        = models.CharField(max_length=50)
    session_year = models.CharField(max_length=20)
    file         = models.FileField(upload_to='uploads/admission/')
    is_active    = models.BooleanField(default=True)
    uploaded_by  = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                       on_delete=models.SET_NULL, related_name='+')
    uploaded_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Admission Result Upload"

    def __str__(self):
        return self.label


# ─────────────────────────────────────────────────────────────────────────────
# GALLERY / EVENTS / NOTICES
# ─────────────────────────────────────────────────────────────────────────────

class GalleryAlbum(models.Model):
    title        = models.CharField(max_length=200)
    slug         = models.SlugField(unique=True, blank=True)
    cover_image  = models.ImageField(upload_to='gallery/covers/', blank=True, null=True)
    description  = models.TextField(blank=True, null=True)
    date         = models.DateField(null=True, blank=True)
    is_published = models.BooleanField(default=True)
    order        = models.PositiveSmallIntegerField(default=0)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', 'order']
        verbose_name = "Gallery Album"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class GalleryPhoto(models.Model):
    album   = models.ForeignKey(GalleryAlbum, on_delete=models.CASCADE,
                  related_name='photos')
    image   = models.ImageField(upload_to='gallery/photos/')
    caption = models.CharField(max_length=200, blank=True, null=True)
    order   = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['album', 'order']

    def __str__(self):
        return f"{self.album.title} — {self.order}"


class Event(models.Model):
    title        = models.CharField(max_length=200)
    slug         = models.SlugField(unique=True, blank=True)
    image        = models.ImageField(upload_to='events/', blank=True, null=True)
    description  = models.TextField(blank=True, null=True)
    venue        = models.CharField(max_length=200, blank=True, null=True)
    event_date   = models.DateField()
    event_time   = models.TimeField(blank=True, null=True)
    is_published = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-event_date']
        verbose_name = "Event"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class Notice(models.Model):
    TARGET_CHOICES = [
        ('all',      'Everyone'),
        ('students', 'Students'),
        ('faculty',  'Faculty & Staff'),
        ('parents',  'Parents'),
    ]
    title           = models.CharField(max_length=300)
    slug            = models.SlugField(unique=True, blank=True)
    content         = models.TextField(blank=True, null=True)
    attachment      = models.FileField(upload_to='notices/', blank=True, null=True)
    target_audience = models.CharField(max_length=20, choices=TARGET_CHOICES, default='all')
    publish_date    = models.DateField()
    expiry_date     = models.DateField(null=True, blank=True)
    is_published    = models.BooleanField(default=False)
    is_pinned       = models.BooleanField(default=False)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_pinned', '-publish_date']
        verbose_name = "Notice"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Only generate a slug if it doesn't exist (e.g., on initial creation)
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            # Loop to find the next available slug
            while Notice.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
            
        super().save(*args, **kwargs)
        
        
    
class Contact(models.Model):
    """Singleton model for holding global contact information."""

    # Logo (shown in navbar and footer)
    logo = models.ImageField(
        upload_to='site/', blank=True, null=True,
        help_text="School logo — shown in the navbar and footer. Upload to replace the default static logo."
    )

    # Mandatory Fields
    email = models.EmailField(max_length=255)
    phone_1 = models.CharField(max_length=20, verbose_name="Primary Phone")

    # Optional Fields
    phone_2 = models.CharField(max_length=20, blank=True, null=True, verbose_name="Secondary Phone")
    address = models.TextField(blank=True, null=True)
    map_embed_url = models.TextField(blank=True, null=True, help_text="Google Maps embed iframe/link")

    class Meta:
        verbose_name = "Contact Information"
        verbose_name_plural = "Contact Information"

    def save(self, *args, **kwargs):
        # Force the primary key to 1 so it always overwrites the same row
        self.pk = 1 
        super(Contact, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Optional: Prevent deletion of the single instance
        pass 

    @classmethod
    def load(cls):
        # Helper method to get the instance or create a blank one if none exists
        obj, created = cls.objects.get_or_create(pk=1, defaults={
            'email': 'admin@school.com', 
            'phone_1': '+0000000000'
        })
        return obj

    def __str__(self):
        return "School Contact Information"


class SocialMedia(models.Model):
    """Singleton model for holding social media URLs."""
    
    facebook = models.URLField(max_length=255, blank=True, null=True)
    instagram = models.URLField(max_length=255, blank=True, null=True)
    linkedin = models.URLField(max_length=255, blank=True, null=True)
    twitter = models.URLField(max_length=255, blank=True, null=True)
    youtube = models.URLField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = "Social Media Links"
        verbose_name_plural = "Social Media Links"

    def save(self, *args, **kwargs):
        # Force the primary key to 1 so it always overwrites the same row
        self.pk = 1 
        super(SocialMedia, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Social Media Links"
        


class Facility(models.Model):
    image       = models.ImageField(upload_to='facilities/', blank=True, null=True)
    heading     = models.CharField(max_length=200, blank=True, null=True)
    slug        = models.SlugField(max_length=250, unique=True, blank=True, null=True)
    description = models.TextField()

    def __str__(self):
        return f"{self.heading}"

    def get_absolute_url(self):
        """Public URL for this facility's detail page."""
        from django.urls import reverse
        if self.slug:
            return reverse('facility_detail', kwargs={'slug': self.slug})
        return '#'

    def save(self, *args, **kwargs):
        if self.heading and not self.slug:
            base_slug = slugify(self.heading)
            slug = base_slug
            counter = 1
            while Facility.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# CURRICULUM STAGES
# ─────────────────────────────────────────────────────────────────────────────

_CURRICULUM_ICONS = [
    'fas fa-baby', 'fas fa-pencil', 'fas fa-book-open',
    'fas fa-flask', 'fas fa-graduation-cap', 'fas fa-star',
    'fas fa-chalkboard-user', 'fas fa-atom',
]


class CurriculumStage(models.Model):
    """
    One card in the "Our Curriculum Stages" swiper on the home page.
    Each stage also gets its own detail page at /curriculum/<slug>/.
    """
    label       = models.CharField(max_length=100,
                      help_text="Short badge label, e.g. 'Nursery & KG'")
    age_group   = models.CharField(max_length=150, blank=True,
                      help_text="Age/class range, e.g. 'Ages 3–5' or 'Classes I–V · Ages 6–10'")
    image       = models.ImageField(upload_to='curriculum/', blank=True, null=True)
    icon_class  = models.CharField(max_length=100, default='fas fa-graduation-cap',
                      help_text="Font Awesome fallback icon when no image is uploaded (auto-assigned)")
    heading     = models.CharField(max_length=200,
                      help_text="Main title on the card, e.g. 'Early Childhood Foundation'")
    description = models.TextField(help_text="Short paragraph about this stage")
    feature_1   = models.CharField(max_length=200, blank=True)
    feature_2   = models.CharField(max_length=200, blank=True)
    feature_3   = models.CharField(max_length=200, blank=True)
    order       = models.PositiveSmallIntegerField(default=0)
    is_active   = models.BooleanField(default=True)
    slug        = models.SlugField(max_length=250, unique=True, blank=True)

    class Meta:
        ordering = ['order']
        verbose_name = "Curriculum Stage"

    def __str__(self):
        return self.label

    def get_absolute_url(self):
        from django.urls import reverse
        if self.slug:
            return reverse('curriculum_detail', kwargs={'slug': self.slug})
        return '#'

    def save(self, *args, **kwargs):
        if not self.slug and self.label:
            base_slug = slugify(self.label)
            slug = base_slug
            counter = 1
            while CurriculumStage.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# HOME PAGE SECTIONS  — editable from the admin panel
# ─────────────────────────────────────────────────────────────────────────────

class HeroStat(models.Model):
    """
    Singleton — the 4 counter items in the floating stats bar below the hero slider.
    Labels, numbers, and suffixes are all editable from the admin panel.
    """
    stat1_count  = models.PositiveIntegerField(default=3200)
    stat1_suffix = models.CharField(max_length=10, default="+")
    stat1_label  = models.CharField(max_length=100, default="Students")

    stat2_count  = models.PositiveIntegerField(default=180)
    stat2_suffix = models.CharField(max_length=10, default="+")
    stat2_label  = models.CharField(max_length=100, default="Faculty Members")

    stat3_count  = models.PositiveIntegerField(default=28)
    stat3_suffix = models.CharField(max_length=10, blank=True, default="")
    stat3_label  = models.CharField(max_length=100, default="Years of Excellence")

    stat4_count  = models.PositiveIntegerField(default=96)
    stat4_suffix = models.CharField(max_length=10, default="%")
    stat4_label  = models.CharField(max_length=100, default="Pass Rate")

    class Meta:
        verbose_name = "Hero Stat Bar"

    def __str__(self):
        return "Hero Stats Bar"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class HomeAbout(models.Model):
    """
    Singleton — controls the 'About Us' section on the home page.
    Heading example: 'A Legacy of Learning, A Future of Leaders'
    """
    section_label   = models.CharField(max_length=100, default="Who We Are")
    heading         = models.CharField(max_length=250, default="A Legacy of Learning, A Future of Leaders")
    lead_text       = models.TextField(help_text="Bold introductory paragraph.")
    body_text       = models.TextField(help_text="Secondary paragraph below the lead.")
    main_image      = models.ImageField(upload_to='home/about/', blank=True, null=True)
    accent_image    = models.ImageField(upload_to='home/about/', blank=True, null=True)
    years_of_excellence = models.PositiveSmallIntegerField(default=28)
    # Three highlight rows
    highlight_1_icon  = models.CharField(max_length=100, default="fas fa-medal")
    highlight_1_title = models.CharField(max_length=150, default="Award-Winning Faculty")
    highlight_1_text  = models.CharField(max_length=200, default="Experienced, passionate educators")
    highlight_2_icon  = models.CharField(max_length=100, default="fas fa-globe")
    highlight_2_title = models.CharField(max_length=150, default="Global Curriculum")
    highlight_2_text  = models.CharField(max_length=200, default="International standards, local values")
    highlight_3_icon  = models.CharField(max_length=100, default="fas fa-heart")
    highlight_3_title = models.CharField(max_length=150, default="Holistic Development")
    highlight_3_text  = models.CharField(max_length=200, default="Academics, arts, sports & character")
    button_label      = models.CharField(max_length=50, blank=True, null=True)
    button_link       = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = "Home — About Section"

    def __str__(self):
        return "About Us Section"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={
            'lead_text': 'Peace International School has been a beacon of educational excellence since 1996.',
            'body_text':  'Our holistic approach blends rigorous academics with creative exploration and community values.',
        })
        return obj


class CorePillar(models.Model):
    """One card in the 'Our Core Pillars' section on the home page."""
    icon_class  = models.CharField(max_length=100, default="fas fa-lightbulb",
                      help_text="Font Awesome class, e.g. 'fas fa-lightbulb'")
    title       = models.CharField(max_length=150)
    description = models.TextField()
    order       = models.PositiveSmallIntegerField(default=0)
    is_active   = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name = "Core Pillar"

    def __str__(self):
        return self.title


class HomeAchievement(models.Model):
    """One counter card in the 'Numbers That Speak' section on the home page."""
    icon_class = models.CharField(max_length=100, default="fas fa-trophy",
                     help_text="Font Awesome class, e.g. 'fas fa-trophy'")
    count      = models.PositiveIntegerField()
    suffix     = models.CharField(max_length=10, blank=True, default="+",
                     help_text="Text after the number, e.g. '+' or '%'")
    label      = models.CharField(max_length=150)
    order      = models.PositiveSmallIntegerField(default=0)
    is_active  = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name = "Home Achievement"

    def __str__(self):
        return self.label