from django.shortcuts import render, get_object_or_404
from django.http import Http404
from django.utils import timezone
import datetime
from backend.models import (
    HomeSlider, HeroStat, HomeAbout, CorePillar, HomeAchievement,
    Facility, CurriculumStage, Event, Notice, Contact, SocialMedia,
    GalleryAlbum, SubMenu, Menu,
)


def home(request):
    today = timezone.now().date()

    # Show 3 upcoming published events.
    # If none exist, fall back to the 3 most recent past events.
    # If there are NO published events at all, home_events is empty
    # and the entire events section is hidden by the template.
    home_events = list(
        Event.objects.filter(is_published=True, event_date__gte=today)
        .order_by('event_date')[:3]
    )
    if not home_events:
        home_events = list(
            Event.objects.filter(is_published=True)
            .order_by('-event_date')[:3]
        )

    context = {
        'sliders':           HomeSlider.objects.filter(is_active=True),
        'hero_stats':        HeroStat.load(),
        'about':             HomeAbout.load(),
        'pillars':           CorePillar.objects.filter(is_active=True).order_by('order'),
        'achievements':      HomeAchievement.objects.filter(is_active=True).order_by('order'),
        'facilities':        Facility.objects.all().order_by('id'),
        'curriculum_stages': CurriculumStage.objects.filter(is_active=True).order_by('order'),
        'home_events':       home_events,
    }
    return render(request, 'school/index.html', context)


def dynamic_page(request, menu_slug, submenu_slug):
    """
    Serves Layout 1 / 2 / 3 pages.
    URL: /page/<menu-slug>/<submenu-slug>/
    """
    submenu = get_object_or_404(
        SubMenu,
        slug=submenu_slug,
        menu__slug=menu_slug,
        is_active=True,
    )
    if submenu.page == 'layout_1':
        return render(request, 'school/dynamic_page/layout_1.html', {
            'submenu':  submenu,
            'sections': submenu.sections.all().order_by('order'),
        })
    if submenu.page == 'layout_2':
        return render(request, 'school/dynamic_page/layout_2.html', {
            'submenu': submenu,
            'photos':  submenu.photos.all().order_by('order'),
        })
    if submenu.page == 'layout_3':
        return render(request, 'school/dynamic_page/layout_3.html', {
            'submenu':    submenu,
            'rich_texts': submenu.rich_texts.all().order_by('order'),
        })
    raise Http404


def direct_menu_page(request, menu_slug):
    """
    Serves Layout 1 / 2 / 3 pages for Menus that have a direct page link set
    (i.e. Menu.page = 'layout_1' / 'layout_2' / 'layout_3', no submenus).
    URL: /page/<menu-slug>/
    """
    menu = get_object_or_404(Menu, slug=menu_slug, is_active=True)
    if menu.page == 'layout_1':
        return render(request, 'school/dynamic_page/layout_1.html', {
            'menu':     menu,
            'submenu':  None,
            'sections': menu.page_sections.all().order_by('order'),
        })
    if menu.page == 'layout_2':
        return render(request, 'school/dynamic_page/layout_2.html', {
            'menu':    menu,
            'submenu': None,
            'photos':  menu.page_photos.all().order_by('order'),
        })
    if menu.page == 'layout_3':
        return render(request, 'school/dynamic_page/layout_3.html', {
            'menu':       menu,
            'submenu':    None,
            'rich_texts': menu.page_rich_texts.all().order_by('order'),
        })
    raise Http404


def galleries(request):
    albums = GalleryAlbum.objects.filter(is_published=True).order_by('-date', 'order')
    return render(request, 'school/galleries/galleries.html', {'albums': albums})


def events(request):
    today = timezone.now().date()
    return render(request, 'school/events/all_events.html', {
        'upcoming_events': Event.objects.filter(
            is_published=True, event_date__gte=today
        ).order_by('event_date'),
        'past_events': Event.objects.filter(
            is_published=True, event_date__lt=today
        ).order_by('-event_date'),
    })


def notices(request):
    today = timezone.now().date()
    seven_days_ago = today - datetime.timedelta(days=7)

    # Published, not yet expired
    qs = Notice.objects.filter(is_published=True, publish_date__lte=today)
    qs = (
        qs.filter(expiry_date__isnull=True) |
        qs.filter(expiry_date__gte=today)
    ).order_by('-is_pinned', '-publish_date')

    notices_list = list(qs)
    pinned  = [n for n in notices_list if n.is_pinned]
    regular = [n for n in notices_list if not n.is_pinned]

    # Audience counts for the sidebar (counts from all visible notices)
    audience_counts = {
        'all':      len(notices_list),
        'students': sum(1 for n in notices_list if n.target_audience == 'students'),
        'faculty':  sum(1 for n in notices_list if n.target_audience == 'faculty'),
        'parents':  sum(1 for n in notices_list if n.target_audience == 'parents'),
    }

    return render(request, 'school/notices/all_notices.html', {
        'pinned_notices':  pinned,
        'regular_notices': regular,
        'all_notices':     notices_list,
        'audience_counts': audience_counts,
        'seven_days_ago':  seven_days_ago,
        'today':           today,
    })


def facility_detail(request, slug):
    """Dedicated detail page for a single Facility."""
    facility = get_object_or_404(Facility, slug=slug)
    return render(request, 'school/facilities/facility_detail.html', {'facility': facility})


def curriculum_detail(request, slug):
    """Dedicated detail page for a single Curriculum Stage."""
    stage = get_object_or_404(CurriculumStage, slug=slug, is_active=True)
    return render(request, 'school/curriculum/curriculum_detail.html', {'stage': stage})


def contact(request):
    return render(request, 'school/contact/contact.html', {
        'contact': Contact.load(),
        'social':  SocialMedia.load(),
    })
