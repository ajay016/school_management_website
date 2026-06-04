from django.db.models import Prefetch
from .models import Menu, SubMenu, Contact, SocialMedia, Facility, CurriculumStage


def navbar_menus(request):
    """
    Injected into every template context:
    - nav_menus:      ordered active Menu tree (active submenus pre-fetched)
    - nav_contact:    singleton Contact
    - nav_social:     singleton SocialMedia
    - nav_facilities: all Facility objects (for the facilities_list dropdown)
    - nav_curriculum: active CurriculumStage objects (for the curriculum_list dropdown)
    """
    menus = (
        Menu.objects
        .filter(is_active=True)
        .prefetch_related(
            Prefetch(
                'submenus',
                queryset=SubMenu.objects.filter(is_active=True).order_by('order'),
            )
        )
        .order_by('order')
    )
    return {
        'nav_menus':      menus,
        'nav_contact':    Contact.load(),
        'nav_social':     SocialMedia.load(),
        'nav_facilities': Facility.objects.all().order_by('id'),
        'nav_curriculum': CurriculumStage.objects.filter(is_active=True).order_by('order'),
    }
