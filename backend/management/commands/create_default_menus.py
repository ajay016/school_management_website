"""
Usage:
    python manage.py create_default_menus

Creates (or repairs) the standard school website menu structure.
Safe to run multiple times — skips menus that already exist and
updates the page types for Facilities and Curriculum if they were
previously created with page=None.
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from backend.models import Menu


# (name, page_type, order)
# facilities_list / curriculum_list = model-driven dropdowns (no SubMenu needed)
DEFAULT_MENUS = [
    ('About Us',   None,              1),
    ('Admission',  None,              2),
    ('Curriculum', 'curriculum_list', 3),
    ('Facilities', 'facilities_list', 4),
    ('Rules',      None,              5),
    ('Gallery',    'gallery',         6),
    ('Notices',    'notices',         7),
    ('Events',     'events',          8),
    ('Contact',    'contact',         9),
]


class Command(BaseCommand):
    help = 'Create (or repair) default navbar menu items for a school website.'

    def handle(self, *args, **options):
        created = repaired = skipped = 0

        for name, page, order in DEFAULT_MENUS:
            slug = slugify(name)
            try:
                menu = Menu.objects.get(slug=slug)
                # Repair: set correct page type if it differs
                if menu.page != page:
                    menu.page = page
                    menu.save(update_fields=['page'])
                    self.stdout.write(self.style.WARNING(f'  REPAIRED  {name}  (page -> {page or "None"})'))
                    repaired += 1
                else:
                    self.stdout.write(f'  SKIP      {name}  (already correct)')
                    skipped += 1
            except Menu.DoesNotExist:
                Menu.objects.create(name=name, page=page, order=order, is_active=True)
                self.stdout.write(self.style.SUCCESS(f'  CREATED   {name}'))
                created += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done. {created} created, {repaired} repaired, {skipped} skipped.'
        ))
        self.stdout.write(
            '\nNext steps:\n'
            '  Facilities  -> Admin: Facilities > Add Facility\n'
            '  Curriculum  -> Admin: Curriculum > Add Stage\n'
            '  Other menus -> Admin: Navbar Menus > edit menu > add submenus (page = Layout 1)\n'
        )
