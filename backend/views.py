from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model, logout
from django.http import JsonResponse, HttpResponse
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django.db import transaction
from django.db.models import Q, F, Count
from django.utils import timezone
import logging
import json
from .models import *
from .models import _CURRICULUM_ICONS











User = get_user_model()
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: parse the unified assignment field from layout create/edit forms.
# Value is either "submenu_<int>" (or plain "<int>") for a SubMenu assignment,
# or "menu_<int>" for a direct Menu assignment.
# Returns ('submenu', id) or ('menu', id).
# ─────────────────────────────────────────────────────────────────────────────
def _parse_assignment(raw_id):
    raw = str(raw_id).strip()
    if raw.startswith('menu_'):
        return 'menu', int(raw[5:])
    return 'submenu', int(raw)


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: return the eligible direct-menu objects for a given layout type.
# Eligible = has the matching page value, is_active, NO submenus, and
# (for create) no existing content, or (for edit) content belongs to this menu.
# ─────────────────────────────────────────────────────────────────────────────
def _eligible_menus(page_type, content_related_name, exclude_menu_id=None):
    """
    page_type            e.g. 'layout_1'
    content_related_name e.g. 'page_sections'
    exclude_menu_id      ID of the menu currently assigned to the item being
                         edited (so it still appears in the dropdown).
    """
    from django.db.models import Count, Q
    qs = Menu.objects.filter(page=page_type, is_active=True).annotate(
        sub_count=Count('submenus', distinct=True),
        content_count=Count(content_related_name, distinct=True),
    ).filter(sub_count=0)  # only leaf menus (no submenu dropdown)

    if exclude_menu_id:
        qs = qs.filter(Q(content_count=0) | Q(id=exclude_menu_id))
    else:
        qs = qs.filter(content_count=0)

    return qs




def admin_dashboard(request):
    import datetime
    today = timezone.now().date()

    # ── Notices ──────────────────────────────────────────────────────────────
    total_notices     = Notice.objects.count()
    published_notices = Notice.objects.filter(is_published=True).count()
    pinned_notices    = Notice.objects.filter(is_pinned=True).count()
    recent_notices    = Notice.objects.order_by('-created_at')[:6]

    # ── Events ───────────────────────────────────────────────────────────────
    total_events    = Event.objects.count()
    upcoming_count  = Event.objects.filter(event_date__gte=today).count()
    upcoming_events = Event.objects.filter(
        event_date__gte=today, is_published=True
    ).order_by('event_date')[:5]

    # ── Gallery ───────────────────────────────────────────────────────────────
    total_albums        = GalleryAlbum.objects.count()
    total_gallery_photos = GalleryPhoto.objects.count()

    # ── Navigation ───────────────────────────────────────────────────────────
    total_menus    = Menu.objects.filter(is_active=True).count()
    total_submenus = SubMenu.objects.filter(is_active=True).count()

    # ── Page Content ─────────────────────────────────────────────────────────
    total_sections    = PageSection.objects.count()
    total_page_photos = PagePhoto.objects.count()
    total_rich_texts  = PageRichText.objects.count()

    # ── Uploads ───────────────────────────────────────────────────────────────
    total_faculty_uploads   = FacultyUpload.objects.count()
    total_student_uploads   = StudentUpload.objects.count()
    total_result_uploads    = ResultUpload.objects.count()
    total_admission_uploads = AdmissionResultUpload.objects.count()
    total_uploads = total_faculty_uploads + total_student_uploads + total_result_uploads + total_admission_uploads

    # ── Sliders ───────────────────────────────────────────────────────────────
    total_sliders = HomeSlider.objects.count()

    return render(request, 'backend/dashboard/admin_dashboard.html', {
        'today':                 today,
        # notices
        'total_notices':         total_notices,
        'published_notices':     published_notices,
        'pinned_notices':        pinned_notices,
        'recent_notices':        recent_notices,
        # events
        'total_events':          total_events,
        'upcoming_count':        upcoming_count,
        'upcoming_events':       upcoming_events,
        # gallery
        'total_albums':          total_albums,
        'total_gallery_photos':  total_gallery_photos,
        # navigation
        'total_menus':           total_menus,
        'total_submenus':        total_submenus,
        # content
        'total_sections':        total_sections,
        'total_page_photos':     total_page_photos,
        'total_rich_texts':      total_rich_texts,
        # uploads
        'total_faculty_uploads':   total_faculty_uploads,
        'total_student_uploads':   total_student_uploads,
        'total_result_uploads':    total_result_uploads,
        'total_admission_uploads': total_admission_uploads,
        'total_uploads':           total_uploads,
        # misc
        'total_sliders':         total_sliders,
    })


def create_home_slider(request):
    if request.method == 'POST':
        # Create instance from POST and FILES
        slider = HomeSlider(
            greeting_badge=request.POST.get('greeting_badge'),
            heading=request.POST.get('heading'),
            short_description=request.POST.get('short_description'),
            button_label=request.POST.get('button_label'),
            button_link=request.POST.get('button_link'),
            is_active=request.POST.get('is_active') == 'true',
        )
        
        # Attach files if they exist
        if 'slider_image' in request.FILES:
            slider.slider_image = request.FILES['slider_image']
        if 'hero_image' in request.FILES:
            slider.hero_image = request.FILES['hero_image']

        try:
            # This triggers the model's clean() method for all validations
            slider.full_clean()
            slider.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Slider created successfully!'
            })
            
        except ValidationError as e:
            # Extract specific field errors or non-field errors
            error_dict = e.message_dict if hasattr(e, 'message_dict') else {'__all__': e.messages}
            return JsonResponse({
                'success': False,
                'message': 'Please correct the errors below.',
                'errors': error_dict
            }, status=400)

    return render(request, 'backend/sliders/create_slider.html')


def list_home_sliders(request):
    sliders = HomeSlider.objects.all()
    return render(request, 'backend/sliders/list_sliders.html', {'sliders': sliders})

def delete_home_slider(request, pk):
    if request.method == 'POST':
        slider = get_object_or_404(HomeSlider, pk=pk)
        try:
            slider.delete()
            return JsonResponse({
                'success': True,
                'message': 'Slider deleted successfully!'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'An error occurred while deleting the slider.'
            }, status=500)
            
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)


def edit_home_slider(request, pk):
    slider = get_object_or_404(HomeSlider, pk=pk)

    if request.method == 'POST':
        # Update text fields
        slider.greeting_badge = request.POST.get('greeting_badge')
        slider.heading = request.POST.get('heading')
        slider.short_description = request.POST.get('short_description')
        slider.button_label = request.POST.get('button_label')
        slider.button_link = request.POST.get('button_link')
        slider.is_active = request.POST.get('is_active') == 'true'
        
        # Attach files if new ones are uploaded
        if 'slider_image' in request.FILES:
            slider.slider_image = request.FILES['slider_image']
        if 'hero_image' in request.FILES:
            slider.hero_image = request.FILES['hero_image']

        try:
            # Trigger model validations (character limits, etc.)
            slider.full_clean()
            slider.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Slider updated successfully!'
            })
            
        except ValidationError as e:
            error_dict = e.message_dict if hasattr(e, 'message_dict') else {'__all__': e.messages}
            return JsonResponse({
                'success': False,
                'message': 'Please correct the errors below.',
                'errors': error_dict
            }, status=400)

    return render(request, 'backend/sliders/edit_slider.html', {'slider': slider})



def create_menu(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        order_str = request.POST.get('order', '0').strip()
        page = request.POST.get('page', '').strip()
        is_active_str = request.POST.get('is_active', 'false')
        
        is_active = str(is_active_str).lower() in ['true', 'on', '1']
        
        errors = {}
        
        # --- Name Validation ---
        if not name:
            errors['name'] = ['Menu name is required.']
        elif len(name) > 100:
            errors['name'] = ['Menu name cannot exceed 100 characters.']
        else:
            # Check if the generated slug will trigger a database IntegrityError
            slug = slugify(name)
            if Menu.objects.filter(slug=slug).exists():
                errors['name'] = ['A menu with this name (or similar) already exists.']

        # --- Order Validation ---
        if not order_str:
            errors['order'] = ['Order is required.']
        else:
            try:
                order = int(order_str)
                if order < 0:
                    errors['order'] = ['Order must be a positive number or zero.']
            except ValueError:
                errors['order'] = ['Order must be a valid whole number.']

        # --- Page Layout/Direct Link Validation ---
        valid_pages = [choice[0] for choice in PAGE_CHOICES]
        if page and page not in valid_pages:
            errors['page'] = ['Invalid page layout selection.']

        # --- Active Menu Limit ---
        if is_active:
            active_count = Menu.objects.filter(is_active=True).count()
            if active_count >= 13:
                errors['is_active'] = [
                    'The navbar already has 13 active menus — the maximum allowed for readability. '
                    'Please deactivate another menu before activating this one.'
                ]

        # Return Error JSON if validation fails
        if errors:
            return JsonResponse({
                'success': False,
                'message': 'Please correct the errors below.',
                'errors': errors
            }, status=400)
            
        # --- Save Menu ---
        try:
            Menu.objects.create(
                name=name,
                order=order,
                page=page if page else None,
                is_active=is_active
            )
            return JsonResponse({
                'success': True,
                'message': 'Menu created successfully!'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'An unexpected error occurred.',
                'errors': {'name': [str(e)]}
            }, status=500)
            
    # GET Request: Render form
    context = {
        'page_choices': PAGE_CHOICES
    }
    return render(request, 'backend/navbar_menus/create_menu.html', context)



def list_menus(request):
    """View to list all menus for the datatable."""
    # Ordered by the Meta ordering ('order')
    menus = Menu.objects.all()
    context = {
        'menus': menus
    }
    return render(request, 'backend/navbar_menus/list_menus.html', context)

def edit_menu(request, id):
    """Dummy view to prevent URL reversal errors."""
    return HttpResponse(f"Edit Menu {id} Placeholder. The template will be built later.")

def delete_menu(request, id):
    """AJAX view to delete a menu and re-sequence the order of remaining menus."""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                menu = get_object_or_404(Menu, id=id)
                deleted_order = menu.order
                menu_name = menu.name
                
                # Delete the menu
                menu.delete()
                
                # Re-sequence orders: Shift all menus with an order > deleted_order down by 1
                Menu.objects.filter(order__gt=deleted_order).update(order=F('order') - 1)
                
            return JsonResponse({
                'success': True,
                'message': f'Menu "{menu_name}" deleted successfully and order re-sequenced.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'An error occurred while trying to delete the menu.',
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)


def edit_menu(request, id):
    menu = get_object_or_404(Menu, id=id)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        order_str = request.POST.get('order', '0').strip()
        page = request.POST.get('page', '').strip()
        is_active_str = request.POST.get('is_active', 'false')
        
        is_active = str(is_active_str).lower() in ['true', 'on', '1']
        errors = {}
        
        # Validation
        if not name:
            errors['name'] = ['Menu name is required.']
        else:
            slug = slugify(name)
            if Menu.objects.filter(slug=slug).exclude(id=menu.id).exists():
                errors['name'] = ['Another menu with this name already exists.']

        try:
            order = int(order_str) if order_str else 0
            if order < 0: errors['order'] = ['Order must be 0 or positive.']
        except ValueError:
            errors['order'] = ['Order must be a valid number.']

        valid_pages = [c[0] for c in PAGE_CHOICES]
        if page and page not in valid_pages:
            errors['page'] = ['Invalid page layout selection.']

        # Active menu limit — only check if we're activating a currently-inactive menu
        if is_active and not menu.is_active:
            active_count = Menu.objects.filter(is_active=True).count()
            if active_count >= 13:
                errors['is_active'] = [
                    'The navbar already has 13 active menus — the maximum allowed for readability. '
                    'Please deactivate another menu before activating this one.'
                ]

        if errors:
            return JsonResponse({'success': False, 'message': 'Please correct the errors.', 'errors': errors}, status=400)

        try:
            menu.name = name
            menu.slug = slugify(name) # Update slug if name changes
            menu.order = order
            menu.page = page if page else None
            menu.is_active = is_active
            menu.save()
            return JsonResponse({'success': True, 'message': 'Menu updated successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    # GET Request
    submenus = menu.submenus.all()
    context = {
        'menu': menu,
        'submenus': submenus,
        'page_choices': PAGE_CHOICES
    }
    return render(request, 'backend/navbar_menus/edit_menu.html', context)


# --- SUBMENU AJAX VIEWS ---

def create_submenu(request, menu_id):
    if request.method != 'POST': return JsonResponse({}, status=405)
    menu = get_object_or_404(Menu, id=menu_id)
    
    name = request.POST.get('name', '').strip()
    order_str = request.POST.get('order', '0').strip()
    page = request.POST.get('page', '').strip()
    is_active = str(request.POST.get('is_active', 'false')).lower() in ['true', 'on', '1']
    
    errors = {}
    if not name: errors['name'] = ['Submenu name is required.']
    else:
        if SubMenu.objects.filter(menu=menu, slug=slugify(name)).exists():
            errors['name'] = ['A submenu with this name already exists under this menu.']
            
    try:
        order = int(order_str) if order_str else 0
        if order < 0: errors['order'] = ['Order must be 0 or positive.']
    except ValueError: errors['order'] = ['Invalid number.']
    
    if not page or page not in [c[0] for c in PAGE_CHOICES]:
        errors['page'] = ['A valid page layout must be selected.']

    if errors:
        return JsonResponse({'success': False, 'errors': errors}, status=400)
        
    SubMenu.objects.create(menu=menu, name=name, order=order, page=page, is_active=is_active)
    return JsonResponse({'success': True, 'message': 'Submenu added successfully!'})


def get_submenu(request, id):
    submenu = get_object_or_404(SubMenu, id=id)
    return JsonResponse({
        'id': submenu.id,
        'name': submenu.name,
        'order': submenu.order,
        'page': submenu.page,
        'is_active': submenu.is_active
    })


def update_submenu(request, id):
    if request.method != 'POST': return JsonResponse({}, status=405)
    submenu = get_object_or_404(SubMenu, id=id)
    
    name = request.POST.get('name', '').strip()
    order_str = request.POST.get('order', str(submenu.order)).strip()
    page = request.POST.get('page', '').strip()
    is_active = str(request.POST.get('is_active', 'false')).lower() in ['true', 'on', '1']
    
    errors = {}
    if not name: errors['name'] = ['Submenu name is required.']
    else:
        if SubMenu.objects.filter(menu=submenu.menu, slug=slugify(name)).exclude(id=id).exists():
            errors['name'] = ['Name already exists under this menu.']
            
    try: order = int(order_str)
    except ValueError: errors['order'] = ['Invalid number.']
    
    if not page or page not in [c[0] for c in PAGE_CHOICES]:
        errors['page'] = ['Invalid page layout.']

    if errors: return JsonResponse({'success': False, 'errors': errors}, status=400)
        
    submenu.name = name
    submenu.slug = slugify(name)
    submenu.order = order
    submenu.page = page
    submenu.is_active = is_active
    submenu.save()
    return JsonResponse({'success': True, 'message': 'Submenu updated successfully!'})


def delete_submenu(request, id):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                submenu = get_object_or_404(SubMenu, id=id)
                menu = submenu.menu
                deleted_order = submenu.order
                submenu.delete()
                # Resequence remaining submenus for this menu
                SubMenu.objects.filter(menu=menu, order__gt=deleted_order).update(order=F('order') - 1)
            return JsonResponse({'success': True, 'message': 'Submenu deleted.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
        
        
        
def list_layout1(request):
    raw = PageSection.objects.select_related(
        'submenu', 'submenu__menu', 'menu'
    ).all().order_by('order')
    # Attach a human-readable display_page attribute to each section
    for s in raw:
        if s.submenu:
            s.display_page = f"{s.submenu.menu.name} › {s.submenu.name}"
        elif s.menu:
            s.display_page = f"{s.menu.name} (Direct Page)"
        else:
            s.display_page = "—"
    return render(request, 'backend/layouts/list_layout1.html', {'sections': raw})



def create_page_section(request):
    if request.method == 'POST':
        raw_id   = request.POST.get('submenu_id', '').strip()
        heading  = request.POST.get('heading', '').strip()
        person_name = request.POST.get('person_name', '').strip()
        designation = request.POST.get('designation', '').strip()
        image_align = request.POST.get('image_align', 'left')
        order    = request.POST.get('order', 0)
        body     = request.POST.get('body', '').strip()
        image    = request.FILES.get('image')

        errors = {}

        if not raw_id:
            errors['submenu_id'] = ['Please select a page assignment.']
        if not body or body == '<p><br></p>':
            errors['body'] = ['Body content is required.']
        try:
            order = int(order)
        except (ValueError, TypeError):
            errors['order'] = ['Order must be a valid number.']
        if image and not image.content_type.startswith('image/'):
            errors['image'] = ['Uploaded file must be an image.']

        if errors:
            return JsonResponse({'success': False, 'message': 'Please fix the errors below.', 'errors': errors}, status=400)

        try:
            atype, aid = _parse_assignment(raw_id)
            common = dict(heading=heading, person_name=person_name,
                          designation=designation, image_align=image_align,
                          order=order, body=body, image=image)
            if atype == 'menu':
                menu_obj = Menu.objects.get(id=aid, page='layout_1')
                if PageSection.objects.filter(menu=menu_obj).exists():
                    return JsonResponse({'success': False, 'message': 'Validation error.',
                        'errors': {'submenu_id': ['This menu already has content. Please edit the existing page instead.']}
                    }, status=400)
                PageSection.objects.create(menu=menu_obj, submenu=None, **common)
            else:
                submenu = SubMenu.objects.get(id=aid, page='layout_1')
                if PageSection.objects.filter(submenu=submenu).exists():
                    return JsonResponse({'success': False, 'message': 'Validation error.',
                        'errors': {'submenu_id': ['This submenu already has content. Please edit the existing page instead.']}
                    }, status=400)
                PageSection.objects.create(submenu=submenu, menu=None, **common)

            return JsonResponse({'success': True, 'message': 'Layout 1 section created successfully!'})

        except (Menu.DoesNotExist, SubMenu.DoesNotExist):
            return JsonResponse({'success': False, 'message': 'Invalid assignment.',
                'errors': {'submenu_id': ['The selected page does not exist or is not set to Layout 1.']}
            }, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'A server error occurred while saving.', 'error_detail': str(e)}, status=500)

    # GET — submenus without existing sections + eligible direct-link menus
    submenus = SubMenu.objects.filter(
        page='layout_1', is_active=True, sections__isnull=True
    ).select_related('menu')
    menus = _eligible_menus('layout_1', 'page_sections')
    return render(request, 'backend/layouts/create_layout1.html', {'submenus': submenus, 'menus': menus})



def edit_layout1_section(request, id):
    section = get_object_or_404(PageSection, id=id)

    if request.method == 'POST':
        errors = {}
        raw_id      = request.POST.get('submenu_id', '').strip()
        heading     = request.POST.get('heading', '').strip()
        person_name = request.POST.get('person_name', '').strip()
        designation = request.POST.get('designation', '').strip()
        image_align = request.POST.get('image_align', 'left')
        order       = request.POST.get('order', 0)
        body        = request.POST.get('body', '').strip()

        if not raw_id:
            errors['submenu_id'] = ['Please select a page assignment.']
        if not body or body == '<p><br></p>':
            errors['body'] = ['Body content is required.']
        try:
            order = int(order)
        except (ValueError, TypeError):
            errors['order'] = ['Order must be a valid number.']
        if 'image' in request.FILES:
            if not request.FILES['image'].content_type.startswith('image/'):
                errors['image'] = ['Uploaded file must be an image.']

        if errors:
            return JsonResponse({'success': False, 'message': 'Please fix the errors below.', 'errors': errors}, status=400)

        try:
            atype, aid = _parse_assignment(raw_id)
            section.heading     = heading
            section.person_name = person_name
            section.designation = designation
            section.image_align = image_align
            section.order       = order
            section.body        = body
            if 'image' in request.FILES:
                section.image = request.FILES['image']

            if atype == 'menu':
                menu_obj = Menu.objects.get(id=aid, page='layout_1')
                # If switching to a different menu, ensure it has no other content
                if menu_obj.id != section.menu_id and PageSection.objects.filter(menu=menu_obj).exists():
                    return JsonResponse({'success': False, 'message': 'Validation error.',
                        'errors': {'submenu_id': ['This menu already has content assigned. Please select an empty one.']}
                    }, status=400)
                section.submenu = None
                section.menu    = menu_obj
            else:
                submenu = SubMenu.objects.get(id=aid, page='layout_1')
                if submenu.id != section.submenu_id and PageSection.objects.filter(submenu=submenu).exists():
                    return JsonResponse({'success': False, 'message': 'Validation error.',
                        'errors': {'submenu_id': ['This submenu already has content assigned. Please select an empty one.']}
                    }, status=400)
                section.submenu = submenu
                section.menu    = None

            section.save()
            return JsonResponse({'success': True, 'message': 'Section updated successfully.'})

        except (Menu.DoesNotExist, SubMenu.DoesNotExist):
            return JsonResponse({'success': False, 'message': 'Invalid assignment selected.'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    # GET — eligible submenus (empty or already this section's) + eligible menus
    submenus = SubMenu.objects.filter(
        Q(page='layout_1') &
        (Q(sections__isnull=True) | Q(id=section.submenu_id))
    ).distinct().select_related('menu')

    menus = _eligible_menus('layout_1', 'page_sections', exclude_menu_id=section.menu_id)

    return render(request, 'backend/layouts/edit_layout1.html', {
        'section':            section,
        'submenus':           submenus,
        'menus':              menus,
        'cur_submenu_id':     section.submenu_id,   # int or None
        'cur_menu_id':        section.menu_id,       # int or None
    })



def delete_layout1_section(request, section_id):
    if request.method == 'POST':
        try:
            section = get_object_or_404(PageSection, id=section_id)
            # Django automatically cleans up the image file if you have django-cleanup installed, 
            # otherwise it just deletes the DB record.
            section.delete()
            return JsonResponse({'success': True, 'message': 'Section deleted successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
            
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)



def list_page_photo(request):
    from django.urls import reverse
    items = []
    # SubMenu-based galleries
    for sub in SubMenu.objects.filter(photos__isnull=False, page='layout_2').annotate(
            photo_count=Count('photos')).distinct().select_related('menu'):
        items.append({
            'id':           sub.id,
            'type':         'submenu',
            'display_name': f"{sub.menu.name} › {sub.name}",
            'photo_count':  sub.photo_count,
            'edit_url':     reverse('edit_layout2_gallery', args=[sub.id]),
        })
    # Direct-menu-based galleries
    for menu in Menu.objects.filter(page='layout_2').annotate(
            photo_count=Count('page_photos')).filter(photo_count__gt=0):
        items.append({
            'id':           menu.id,
            'type':         'menu',
            'display_name': f"{menu.name} (Direct Page)",
            'photo_count':  menu.photo_count,
            'edit_url':     reverse('edit_layout2_gallery_menu', args=[menu.id]),
        })
    return render(request, 'backend/layouts/list_layout2.html', {'items': items})


@require_http_methods(["GET", "POST"])
def create_page_photo(request):
    if request.method == "POST":
        raw_id     = request.POST.get('submenu_id', '').strip()
        base_order = request.POST.get('order', 0)
        images     = request.FILES.getlist('images')
        caption    = request.POST.get('captions', '').strip()

        errors = {}
        if not raw_id:
            errors['submenu_id'] = ['Please select a page assignment.']
        if not images:
            errors['images'] = ['Please select at least one image to upload.']
        try:
            base_order = int(base_order)
        except (ValueError, TypeError):
            errors['order'] = ['Order must be a valid integer.']

        if errors:
            return JsonResponse({'success': False, 'message': 'Please fix the errors below.', 'errors': errors}, status=400)

        try:
            atype, aid = _parse_assignment(raw_id)
            if atype == 'menu':
                menu_obj = Menu.objects.get(id=aid, page='layout_2')
                final_caption = caption if caption else menu_obj.name
                for idx, img in enumerate(images):
                    PagePhoto.objects.create(menu=menu_obj, submenu=None, image=img,
                                             caption=final_caption, order=base_order + idx)
            else:
                submenu = SubMenu.objects.get(id=aid, page='layout_2')
                final_caption = caption if caption else submenu.name
                for idx, img in enumerate(images):
                    PagePhoto.objects.create(submenu=submenu, menu=None, image=img,
                                             caption=final_caption, order=base_order + idx)

            return JsonResponse({'success': True, 'message': f'Successfully uploaded {len(images)} photos!'})

        except (Menu.DoesNotExist, SubMenu.DoesNotExist):
            return JsonResponse({'success': False, 'message': 'Invalid assignment.',
                'errors': {'submenu_id': ['The selected page does not exist or is not set to Layout 2.']}
            }, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'A server error occurred while processing the images.', 'error_detail': str(e)}, status=500)

    # GET
    submenus = SubMenu.objects.filter(page='layout_2', is_active=True).select_related('menu')
    menus    = _eligible_menus('layout_2', 'page_photos')
    return render(request, 'backend/layouts/create_layout2.html', {'submenus': submenus, 'menus': menus})
    
    
    
@require_http_methods(["GET", "POST"])
def edit_layout2_gallery(request, submenu_id):
    # Fetch the specific submenu being edited
    current_submenu = get_object_or_404(SubMenu, id=submenu_id, page='layout_2')

    if request.method == "POST":
        # Handle uploading NEW photos to this existing gallery
        base_order = request.POST.get('order', 0)
        images = request.FILES.getlist('images')
        # Grab the caption as a single string and remove extra whitespace
        caption = request.POST.get('captions', '').strip()

        errors = {}

        if not images:
            errors['images'] = ['Please select at least one image to upload.']
        
        try:
            base_order = int(base_order)
        except ValueError:
            errors['order'] = ['Order must be a valid integer.']

        if errors:
            return JsonResponse({
                'success': False,
                'message': 'Please fix the errors below.',
                'errors': errors
            }, status=400)

        try:
            # If no caption is provided, default to the SubMenu name
            final_caption = caption if caption else current_submenu.name

            # Loop ONLY over images, and apply the single caption to all of them
            for index, img in enumerate(images):
                PagePhoto.objects.create(
                    submenu=current_submenu,
                    image=img,
                    caption=final_caption,  # Use the fallback caption here
                    order=base_order + index
                )

            return JsonResponse({
                'success': True,
                'message': f'Successfully added {len(images)} new photos to the gallery!'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'A server error occurred while processing the images.',
                'error_detail': str(e)
            }, status=500)

    # GET Request: Prepare data for the template
    # Get all submenus for the dropdown (in case they want to switch context, though usually disabled)
    submenus = SubMenu.objects.filter(page='layout_2', is_active=True).select_related('menu')
    
    # Get existing photos for the grid
    existing_photos = current_submenu.photos.all().order_by('order', '-id')

    return render(request, 'backend/layouts/edit_layout2.html', {
        'current_submenu': current_submenu,
        'submenus': submenus,
        'existing_photos': existing_photos
    })

@require_http_methods(["GET", "POST"])
def edit_layout2_gallery_menu(request, menu_id):
    """Edit / add photos for a direct-menu Layout 2 gallery."""
    current_menu = get_object_or_404(Menu, id=menu_id, page='layout_2')

    if request.method == "POST":
        base_order = request.POST.get('order', 0)
        images = request.FILES.getlist('images')
        caption = request.POST.get('captions', '').strip()
        errors = {}
        if not images:
            errors['images'] = ['Please select at least one image to upload.']
        try:
            base_order = int(base_order)
        except (ValueError, TypeError):
            errors['order'] = ['Order must be a valid integer.']
        if errors:
            return JsonResponse({'success': False, 'message': 'Please fix the errors below.', 'errors': errors}, status=400)
        try:
            final_caption = caption if caption else current_menu.name
            for idx, img in enumerate(images):
                PagePhoto.objects.create(menu=current_menu, submenu=None, image=img,
                                         caption=final_caption, order=base_order + idx)
            return JsonResponse({'success': True, 'message': f'Successfully added {len(images)} new photos!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'A server error occurred.', 'error_detail': str(e)}, status=500)

    existing_photos = current_menu.page_photos.all().order_by('order', '-id')
    return render(request, 'backend/layouts/edit_layout2.html', {
        'current_submenu': None,
        'current_menu':    current_menu,
        'existing_photos': existing_photos,
    })


@require_POST
def delete_gallery_menu(request, menu_id):
    """Delete all photos for a direct-menu gallery."""
    try:
        menu = get_object_or_404(Menu, id=menu_id)
        PagePhoto.objects.filter(menu=menu).delete()
        return JsonResponse({'success': True, 'message': 'Gallery deleted successfully!'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'Error deleting the gallery.', 'error_detail': str(e)}, status=400)


@require_POST
def delete_single_photo(request, photo_id):
    try:
        photo = get_object_or_404(PagePhoto, id=photo_id)
        photo.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Photo removed permanently.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Error deleting the photo.',
            'error_detail': str(e)
        }, status=400)
    
    

@require_POST
def delete_gallery(request, submenu_id):
    try:
        submenu = get_object_or_404(SubMenu, id=submenu_id)
        # Delete all photos related to this submenu
        PagePhoto.objects.filter(submenu=submenu).delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Entire gallery deleted successfully!'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Error deleting the gallery.',
            'error_detail': str(e)
        }, status=400)
        
        

def list_layout3_rich_text(request):
    from django.urls import reverse
    items = []
    # SubMenu-based
    for sub in SubMenu.objects.filter(page='layout_3').annotate(
            block_count=Count('rich_texts')).select_related('menu').order_by('menu__order', 'order'):
        items.append({
            'id':           sub.id,
            'type':         'submenu',
            'display_name': f"{sub.menu.name} › {sub.name}",
            'block_count':  sub.block_count,
            'edit_url':     reverse('edit_layout3_rich_text', args=[sub.id]),
        })
    # Direct-menu-based
    for menu in Menu.objects.filter(page='layout_3').annotate(
            block_count=Count('page_rich_texts')).filter(block_count__gt=0).order_by('order'):
        items.append({
            'id':           menu.id,
            'type':         'menu',
            'display_name': f"{menu.name} (Direct Page)",
            'block_count':  menu.block_count,
            'edit_url':     reverse('edit_layout3_rich_text_menu', args=[menu.id]),
        })
    return render(request, 'backend/layouts/list_layout3.html', {'items': items})
        
        
        
@require_http_methods(["GET", "POST"])
def create_page_rich_text(request):
    if request.method == "POST":
        raw_id        = request.POST.get('submenu_id', '').strip()
        section_title = request.POST.get('section_title', '').strip()
        content       = request.POST.get('content', '').strip()
        order         = request.POST.get('order', 0)

        errors = {}
        if not raw_id:
            errors['submenu_id'] = ['Please select a page assignment.']
        if not content or content == '<p><br></p>':
            errors['content'] = ['Content cannot be empty.']
        try:
            order = int(order)
        except (ValueError, TypeError):
            errors['order'] = ['Order must be a valid integer.']

        if errors:
            return JsonResponse({'success': False, 'message': 'Please fix the errors below.', 'errors': errors}, status=400)

        try:
            atype, aid = _parse_assignment(raw_id)
            common = dict(section_title=section_title, content=content, order=order)
            if atype == 'menu':
                menu_obj = Menu.objects.get(id=aid, page='layout_3')
                if PageRichText.objects.filter(menu=menu_obj).exists():
                    return JsonResponse({'success': False, 'message': 'Validation error.',
                        'errors': {'submenu_id': ['This menu already has content. Please edit the existing page instead.']}
                    }, status=400)
                PageRichText.objects.create(menu=menu_obj, submenu=None, **common)
            else:
                submenu = SubMenu.objects.get(id=aid, page='layout_3')
                if PageRichText.objects.filter(submenu=submenu).exists():
                    return JsonResponse({'success': False, 'message': 'Validation error.',
                        'errors': {'submenu_id': ['This submenu already has content. Please edit the existing page instead.']}
                    }, status=400)
                PageRichText.objects.create(submenu=submenu, menu=None, **common)

            return JsonResponse({'success': True, 'message': 'Rich text block created successfully!'})

        except (Menu.DoesNotExist, SubMenu.DoesNotExist):
            return JsonResponse({'success': False, 'message': 'Invalid assignment.',
                'errors': {'submenu_id': ['The selected page does not exist or is not set to Layout 3.']}
            }, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'A server error occurred while saving.', 'error_detail': str(e)}, status=500)

    # GET
    submenus = SubMenu.objects.filter(
        page='layout_3', is_active=True, rich_texts__isnull=True
    ).select_related('menu')
    menus = _eligible_menus('layout_3', 'page_rich_texts')
    return render(request, 'backend/layouts/create_layout3.html', {'submenus': submenus, 'menus': menus})
    
    
    
@require_http_methods(["POST"])
def delete_all_layout3_blocks(request, submenu_id):
    """AJAX endpoint to clear all Rich Text blocks for a specific submenu."""
    submenu = get_object_or_404(SubMenu, id=submenu_id, page='layout_3')
    
    try:
        # Delete all PageRichText objects related to this submenu
        deleted_count, _ = submenu.rich_texts.all().delete()
        return JsonResponse({
            'success': True,
            'message': f'Successfully deleted {deleted_count} content blocks.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Failed to delete content blocks.',
            'error_detail': str(e)
        }, status=500)

@require_http_methods(["GET", "POST"])
def edit_layout3_rich_text_menu(request, menu_id):
    """Edit the rich-text content for a direct-menu Layout 3 page."""
    current_menu = get_object_or_404(Menu, id=menu_id, page='layout_3')
    rich_text = current_menu.page_rich_texts.first()

    if request.method == "POST":
        section_title = request.POST.get('section_title', '').strip()
        content       = request.POST.get('content', '').strip()
        order         = request.POST.get('order', 0)
        errors = {}
        if not content or content == '<p><br></p>':
            errors['content'] = ['Content cannot be empty.']
        try:
            order = int(order)
        except (ValueError, TypeError):
            errors['order'] = ['Order must be a valid integer.']
        if errors:
            return JsonResponse({'success': False, 'message': 'Please fix the errors below.', 'errors': errors}, status=400)
        try:
            if rich_text:
                rich_text.section_title = section_title
                rich_text.content       = content
                rich_text.order         = order
                rich_text.save()
            else:
                PageRichText.objects.create(menu=current_menu, submenu=None,
                                            section_title=section_title, content=content, order=order)
            return JsonResponse({'success': True, 'message': 'Rich text content updated successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'A server error occurred.', 'error_detail': str(e)}, status=500)

    return render(request, 'backend/layouts/edit_layout3.html', {
        'current_submenu': None,
        'current_menu':    current_menu,
        'rich_text':       rich_text,
    })


@require_http_methods(["POST"])
def delete_all_layout3_blocks_menu(request, menu_id):
    """Delete all rich-text blocks for a direct-menu Layout 3 page."""
    menu = get_object_or_404(Menu, id=menu_id, page='layout_3')
    try:
        deleted_count, _ = menu.page_rich_texts.all().delete()
        return JsonResponse({'success': True, 'message': f'Successfully deleted {deleted_count} content blocks.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'Failed to delete content blocks.', 'error_detail': str(e)}, status=500)


# Temporary placeholder for the edit view so the URL pattern resolves
@require_http_methods(["GET", "POST"])
def edit_layout3_rich_text(request, submenu_id):
    current_submenu = get_object_or_404(SubMenu, id=submenu_id, page='layout_3')
    
    # Enforce the "only one instance" rule: fetch the existing block
    rich_text = current_submenu.rich_texts.first()

    if request.method == "POST":
        section_title = request.POST.get('section_title', '').strip()
        content = request.POST.get('content', '').strip()
        order = request.POST.get('order', 0)

        errors = {}

        # Validation
        if not content or content == '<p><br></p>':
            errors['content'] = ['Content cannot be empty.']

        try:
            order = int(order)
        except ValueError:
            errors['order'] = ['Order must be a valid integer.']

        if errors:
            return JsonResponse({
                'success': False,
                'message': 'Please fix the errors below.',
                'errors': errors
            }, status=400)

        # Process and Save/Update
        try:
            if rich_text:
                # Update existing
                rich_text.section_title = section_title
                rich_text.content = content
                rich_text.order = order
                rich_text.save()
            else:
                # Create if it mysteriously doesn't exist yet
                PageRichText.objects.create(
                    submenu=current_submenu,
                    section_title=section_title,
                    content=content,
                    order=order
                )

            return JsonResponse({
                'success': True,
                'message': 'Rich text content updated successfully!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'A server error occurred while updating.',
                'error_detail': str(e)
            }, status=500)

    # GET Request: Render the template
    return render(request, 'backend/layouts/edit_layout3.html', {
        'current_submenu': current_submenu,
        'rich_text': rich_text
    })
    
    
    
@require_http_methods(["GET"])
def notice_list(request):
    # This will automatically order by '-is_pinned' and '-publish_date' because of your Meta class
    notices = Notice.objects.all()
    return render(request, 'backend/notices/notice_list.html', {'notices': notices})
    
    
    
@require_http_methods(["GET", "POST"])
def create_notice(request):
    if request.method == "POST":
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        publish_date = request.POST.get('publish_date')
        expiry_date = request.POST.get('expiry_date')
        
        # Boolean checkboxes: if they are checked, they send 'on'
        is_published = request.POST.get('is_published') == 'on'
        is_pinned = request.POST.get('is_pinned') == 'on'
        
        attachment = request.FILES.get('attachment')

        errors = {}

        # Validation
        if not title:
            errors['title'] = ['Title is required.']
        if not publish_date:
            errors['publish_date'] = ['Publish date is required.']
        
        if errors:
            return JsonResponse({
                'success': False,
                'message': 'Please fix the errors below.',
                'errors': errors
            }, status=400)

        target_audience = request.POST.get('target_audience', 'all').strip()
        valid_audiences = [c[0] for c in Notice.TARGET_CHOICES]
        if target_audience not in valid_audiences:
            target_audience = 'all'

        # Process and Save
        try:
            Notice.objects.create(
                title=title,
                content=content,
                publish_date=publish_date,
                expiry_date=expiry_date if expiry_date else None,
                is_published=is_published,
                is_pinned=is_pinned,
                attachment=attachment,
                target_audience=target_audience,
            )

            return JsonResponse({
                'success': True,
                'message': 'Notice created successfully!'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'A server error occurred while saving.',
                'error_detail': str(e)
            }, status=500)

    # GET Request: Render the template
    return render(request, 'backend/notices/create_notice.html', {
        'target_choices': Notice.TARGET_CHOICES,
    })


@require_http_methods(["POST"])
def delete_notice(request, id):
    try:
        notice = get_object_or_404(Notice, id=id)
        notice.delete()
        return JsonResponse({'success': True, 'message': 'Notice deleted successfully.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
    
    

@require_http_methods(["GET", "POST"])
def edit_notice(request, id):
    notice = get_object_or_404(Notice, id=id)

    if request.method == "POST":
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        expiry_date = request.POST.get('expiry_date')
        
        is_published = request.POST.get('is_published') == 'on'
        is_pinned = request.POST.get('is_pinned') == 'on'

        # Smart Publish Date Logic
        if is_published:
            publish_date = timezone.now().date()
        else:
            publish_date = request.POST.get('publish_date')

        errors = {}

        # Validation
        if not title:
            errors['title'] = ['Title is required.']
        if not is_published and not publish_date:
            errors['publish_date'] = ['Publish date is required if not publishing immediately.']
        
        if errors:
            return JsonResponse({
                'success': False,
                'message': 'Please fix the errors below.',
                'errors': errors
            }, status=400)

        target_audience = request.POST.get('target_audience', 'all').strip()
        valid_audiences = [c[0] for c in Notice.TARGET_CHOICES]
        if target_audience not in valid_audiences:
            target_audience = 'all'

        # Process and Save
        try:
            notice.title           = title
            notice.content         = content
            notice.publish_date    = publish_date
            notice.expiry_date     = expiry_date if expiry_date else None
            notice.is_published    = is_published
            notice.is_pinned       = is_pinned
            notice.target_audience = target_audience

            # Only update the attachment if a new file is uploaded
            if 'attachment' in request.FILES:
                notice.attachment = request.FILES['attachment']

            notice.save()

            return JsonResponse({
                'success': True,
                'message': 'Notice updated successfully!'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'A server error occurred while saving.',
                'error_detail': str(e)
            }, status=500)

    # GET Request: Render the template with the instance
    return render(request, 'backend/notices/edit_notice.html', {
        'notice':         notice,
        'target_choices': Notice.TARGET_CHOICES,
    })



# =========================================================
# EVENTS
# =========================================================
 
def create_event(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            title = request.POST.get('title', '').strip()
            if not title:
                return JsonResponse({'success': False, 'message': 'Event title is required.'})
 
            event_date = request.POST.get('event_date', '').strip()
            if not event_date:
                return JsonResponse({'success': False, 'message': 'Event date is required.'})
 
            event = Event(
                title=title,
                description=request.POST.get('description', ''),
                venue=request.POST.get('venue', '').strip(),
                event_date=event_date,
                is_published=request.POST.get('is_published') == 'on',
            )
            event_time = request.POST.get('event_time', '').strip()
            if event_time:
                event.event_time = event_time
            if 'image' in request.FILES:
                event.image = request.FILES['image']
            event.save()
 
            return JsonResponse({'success': True, 'message': f'Event "{event.title}" created successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
 
    return render(request, 'backend/events/create_event.html')
 
 
def event_list(request):
    events = Event.objects.all()
    return render(request, 'backend/events/event_list.html', {'events': events})
 
 
def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
 
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            title = request.POST.get('title', '').strip()
            if not title:
                return JsonResponse({'success': False, 'message': 'Event title is required.'})
 
            event_date = request.POST.get('event_date', '').strip()
            if not event_date:
                return JsonResponse({'success': False, 'message': 'Event date is required.'})
 
            event.title = title
            event.description = request.POST.get('description', '')
            event.venue = request.POST.get('venue', '').strip()
            event.event_date = event_date
            event.is_published = request.POST.get('is_published') == 'on'
 
            event_time = request.POST.get('event_time', '').strip()
            event.event_time = event_time if event_time else None
 
            if 'image' in request.FILES:
                event.image = request.FILES['image']
            event.save()
 
            return JsonResponse({'success': True, 'message': 'Event updated successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
 
    return render(request, 'backend/events/edit_event.html', {'event': event})
 
 
def delete_event(request, event_id):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        event = get_object_or_404(Event, id=event_id)
        title = event.title
        event.delete()
        return JsonResponse({'success': True, 'message': f'Event "{title}" deleted.'})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)
 
 
# =========================================================
# GALLERY ALBUMS & PHOTOS
# =========================================================
 
def create_album(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            title = request.POST.get('title', '').strip()
            if not title:
                return JsonResponse({'success': False, 'message': 'Album title is required.'})
 
            album = GalleryAlbum(
                title=title,
                description=request.POST.get('description', ''),
                is_published=request.POST.get('is_published') == 'on',
                order=int(request.POST.get('order', 0) or 0),
            )
            date_val = request.POST.get('date', '').strip()
            if date_val:
                album.date = date_val
            if 'cover_image' in request.FILES:
                album.cover_image = request.FILES['cover_image']
            album.save()
 
            photos = request.FILES.getlist('photos')
            captions = request.POST.getlist('captions')
            for i, photo in enumerate(photos):
                GalleryPhoto.objects.create(
                    album=album,
                    image=photo,
                    caption=captions[i] if i < len(captions) else '',
                    order=i,
                )
 
            return JsonResponse({
                'success': True,
                'message': f'Album "{album.title}" created with {len(photos)} photo(s)!'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
 
    return render(request, 'backend/galleries/create_album.html')
 
 
def album_list(request):
    albums = GalleryAlbum.objects.prefetch_related('photos').all()
    return render(request, 'backend/galleries/album_list.html', {'albums': albums})
 
 
def edit_album(request, album_id):
    album = get_object_or_404(GalleryAlbum, id=album_id)
 
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            title = request.POST.get('title', '').strip()
            if not title:
                return JsonResponse({'success': False, 'message': 'Album title is required.'})
 
            album.title = title
            album.description = request.POST.get('description', '')
            album.is_published = request.POST.get('is_published') == 'on'
            album.order = int(request.POST.get('order', 0) or 0)
 
            date_val = request.POST.get('date', '').strip()
            if date_val:
                album.date = date_val
 
            if 'cover_image' in request.FILES:
                album.cover_image = request.FILES['cover_image']
            album.save()
 
            new_photos = request.FILES.getlist('new_photos')
            new_captions = request.POST.getlist('new_captions')
            offset = album.photos.count()
            for i, photo in enumerate(new_photos):
                GalleryPhoto.objects.create(
                    album=album,
                    image=photo,
                    caption=new_captions[i] if i < len(new_captions) else '',
                    order=offset + i,
                )
 
            return JsonResponse({
                'success': True,
                'message': f'Album updated! {len(new_photos)} new photo(s) added.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
 
    photos = album.photos.all()
    return render(request, 'backend/galleries/edit_album.html', {'album': album, 'photos': photos})
 
 
def delete_album(request, album_id):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        album = get_object_or_404(GalleryAlbum, id=album_id)
        title = album.title
        album.delete()
        return JsonResponse({'success': True, 'message': f'Album "{title}" deleted.'})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)
 
 
def delete_photo(request, photo_id):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        photo = get_object_or_404(GalleryPhoto, id=photo_id)
        photo.delete()
        return JsonResponse({'success': True, 'message': 'Photo removed from album.'})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)



def edit_contact(request):
    contact = Contact.load()
    social  = SocialMedia.load()

    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            email   = request.POST.get('email',   '').strip()
            phone_1 = request.POST.get('phone_1', '').strip()

            if not email:
                return JsonResponse({'success': False, 'message': 'Email address is required.'})
            if not phone_1:
                return JsonResponse({'success': False, 'message': 'Primary phone number is required.'})

            contact.email         = email
            contact.phone_1       = phone_1
            contact.phone_2       = request.POST.get('phone_2',       '').strip()
            contact.address       = request.POST.get('address',       '').strip()
            contact.map_embed_url = request.POST.get('map_embed_url', '').strip()

            # Logo upload
            if 'logo' in request.FILES:
                logo = request.FILES['logo']
                if logo.content_type.startswith('image/'):
                    contact.logo = logo
                else:
                    return JsonResponse({'success': False, 'message': 'Logo must be an image file.'})

            contact.save()

            social.facebook  = request.POST.get('facebook',  '').strip()
            social.instagram = request.POST.get('instagram', '').strip()
            social.linkedin  = request.POST.get('linkedin',  '').strip()
            social.twitter   = request.POST.get('twitter',   '').strip()
            social.youtube   = request.POST.get('youtube',   '').strip()
            social.save()

            return JsonResponse({'success': True, 'message': 'Settings saved successfully!'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return render(request, 'backend/contact/edit_contact.html', {
        'contact': contact,
        'social':  social,
    })



# Facilities
def list_facilities(request):
    # Fetch all facilities
    facilities = Facility.objects.all().order_by('-id') # You can change the order_by as needed
    return render(request, 'backend/facilities/facilities_list.html', {'facilities': facilities})


# Create Facility
def create_facility(request):
    if request.method == 'POST':
        heading = request.POST.get('heading', '').strip()
        description = request.POST.get('description', '').strip()
        image = request.FILES.get('image')
        
        errors = {}

        # Validation
        if not heading:
            errors['heading'] = ['Heading is required.']
            
        if not description or description == '<p><br></p>':
            errors['description'] = ['Description content is required.']

        if image and not image.content_type.startswith('image/'):
            errors['image'] = ['Uploaded file must be an image.']
                
        if errors:
            return JsonResponse({
                'success': False, 
                'message': 'Please fix the errors below.', 
                'errors': errors
            }, status=400)
            
        try:
            # Create the Facility. The model's save() method handles the unique slug.
            Facility.objects.create(
                heading=heading,
                description=description,
                image=image
            )
            return JsonResponse({
                'success': True, 
                'message': 'Facility created successfully!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'message': 'A server error occurred while saving.', 
                'error_detail': str(e)
            }, status=500)

    # GET Request
    return render(request, 'backend/facilities/create_facility.html')


# Edit Facility
def edit_facility(request, id):
    facility = get_object_or_404(Facility, id=id)
    
    if request.method == 'POST':
        errors = {}
        heading = request.POST.get('heading', '').strip()
        description = request.POST.get('description', '').strip()

        # Validation
        if not heading:
            errors['heading'] = ['Heading is required.']
            
        if not description or description == '<p><br></p>':
            errors['description'] = ['Description content is required.']

        if 'image' in request.FILES:
            image = request.FILES['image']
            if not image.content_type.startswith('image/'):
                errors['image'] = ['Uploaded file must be an image.']

        if errors:
            return JsonResponse({
                'success': False, 
                'message': 'Please fix the errors below.', 
                'errors': errors
            }, status=400)

        # Update Facility details
        try:
            facility.heading = heading
            facility.description = description

            # Only overwrite image if a new one is uploaded
            if 'image' in request.FILES:
                facility.image = request.FILES['image']
                
            facility.save()
            return JsonResponse({'success': True, 'message': 'Facility updated successfully.'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    # GET Request: Load the form with existing data
    return render(request, 'backend/facilities/edit_facility.html', {
        'facility': facility
    })


# Delete Facility
def delete_facility(request, facility_id):
    if request.method == 'POST':
        try:
            facility = get_object_or_404(Facility, id=facility_id)
            facility.delete()
            return JsonResponse({'success': True, 'message': 'Facility deleted successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)


# ─────────────────────────────────────────────────────────────────────────────
# HOME PAGE SECTIONS
# ─────────────────────────────────────────────────────────────────────────────

def edit_hero_stats(request):
    """Singleton — edit the 4 counter stats in the hero stats bar."""
    stats = HeroStat.load()

    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        def to_int(val, default=0):
            try:
                return max(0, int(val or default))
            except (ValueError, TypeError):
                return default

        stats.stat1_count  = to_int(request.POST.get('stat1_count'), 0)
        stats.stat1_suffix = request.POST.get('stat1_suffix', '').strip()
        stats.stat1_label  = request.POST.get('stat1_label', '').strip() or 'Students'
        stats.stat2_count  = to_int(request.POST.get('stat2_count'), 0)
        stats.stat2_suffix = request.POST.get('stat2_suffix', '').strip()
        stats.stat2_label  = request.POST.get('stat2_label', '').strip() or 'Faculty Members'
        stats.stat3_count  = to_int(request.POST.get('stat3_count'), 0)
        stats.stat3_suffix = request.POST.get('stat3_suffix', '').strip()
        stats.stat3_label  = request.POST.get('stat3_label', '').strip() or 'Years of Excellence'
        stats.stat4_count  = to_int(request.POST.get('stat4_count'), 0)
        stats.stat4_suffix = request.POST.get('stat4_suffix', '').strip()
        stats.stat4_label  = request.POST.get('stat4_label', '').strip() or 'Pass Rate'
        stats.save()
        return JsonResponse({'success': True, 'message': 'Hero stats saved successfully!'})

    stat_rows = [
        (1, stats.stat1_count, stats.stat1_suffix, stats.stat1_label),
        (2, stats.stat2_count, stats.stat2_suffix, stats.stat2_label),
        (3, stats.stat3_count, stats.stat3_suffix, stats.stat3_label),
        (4, stats.stat4_count, stats.stat4_suffix, stats.stat4_label),
    ]
    return render(request, 'backend/home/edit_hero_stats.html', {'stats': stats, 'stat_rows': stat_rows})


def edit_home_about(request):
    """Singleton — edit the About Us section on the home page."""
    about = HomeAbout.load()

    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        errors = {}
        heading = request.POST.get('heading', '').strip()
        lead    = request.POST.get('lead_text', '').strip()
        body    = request.POST.get('body_text', '').strip()
        if not heading: errors['heading']   = ['Heading is required.']
        if not lead:    errors['lead_text'] = ['Lead text is required.']
        if not body:    errors['body_text'] = ['Body text is required.']
        if errors:
            return JsonResponse({'success': False, 'message': 'Please fix the errors.', 'errors': errors}, status=400)

        about.section_label       = request.POST.get('section_label', '').strip()
        about.heading             = heading
        about.lead_text           = lead
        about.body_text           = body
        about.years_of_excellence = int(request.POST.get('years_of_excellence') or 28)
        about.highlight_1_icon    = request.POST.get('highlight_1_icon', '').strip()
        about.highlight_1_title   = request.POST.get('highlight_1_title', '').strip()
        about.highlight_1_text    = request.POST.get('highlight_1_text', '').strip()
        about.highlight_2_icon    = request.POST.get('highlight_2_icon', '').strip()
        about.highlight_2_title   = request.POST.get('highlight_2_title', '').strip()
        about.highlight_2_text    = request.POST.get('highlight_2_text', '').strip()
        about.highlight_3_icon    = request.POST.get('highlight_3_icon', '').strip()
        about.highlight_3_title   = request.POST.get('highlight_3_title', '').strip()
        about.highlight_3_text    = request.POST.get('highlight_3_text', '').strip()
        about.button_label        = request.POST.get('button_label', '').strip() or None
        about.button_link         = request.POST.get('button_link', '').strip() or None
        if 'main_image' in request.FILES:
            about.main_image = request.FILES['main_image']
        if 'accent_image' in request.FILES:
            about.accent_image = request.FILES['accent_image']
        about.save()
        return JsonResponse({'success': True, 'message': 'About section saved successfully!'})

    highlight_rows = [
        (1, about.highlight_1_icon, about.highlight_1_title, about.highlight_1_text),
        (2, about.highlight_2_icon, about.highlight_2_title, about.highlight_2_text),
        (3, about.highlight_3_icon, about.highlight_3_title, about.highlight_3_text),
    ]
    return render(request, 'backend/home/edit_about.html', {'about': about, 'highlight_rows': highlight_rows})


# ── Core Pillars ─────────────────────────────────────────────────────────────

def list_core_pillars(request):
    pillars = CorePillar.objects.all()
    return render(request, 'backend/home/pillar_list.html', {'pillars': pillars})


_PILLAR_ICONS = [
    'fas fa-lightbulb', 'fas fa-handshake', 'fas fa-child-reaching',
    'fas fa-earth-asia', 'fas fa-seedling', 'fas fa-users-gear',
    'fas fa-graduation-cap', 'fas fa-heart', 'fas fa-book', 'fas fa-star',
]

def create_core_pillar(request):
    if request.method == 'POST':
        errors = {}
        title = request.POST.get('title', '').strip()
        desc  = request.POST.get('description', '').strip()
        if not title: errors['title']       = ['Title is required.']
        if not desc:  errors['description'] = ['Description is required.']
        if errors:
            return JsonResponse({'success': False, 'message': 'Please fix the errors.', 'errors': errors}, status=400)
        # Auto-assign icon from preset list based on current count (gives visual variety)
        icon = _PILLAR_ICONS[CorePillar.objects.count() % len(_PILLAR_ICONS)]
        CorePillar.objects.create(
            icon_class  = icon,
            title       = title,
            description = desc,
            order       = int(request.POST.get('order') or 0),
            is_active   = request.POST.get('is_active') == 'true',
        )
        return JsonResponse({'success': True, 'message': 'Pillar created successfully!'})
    return render(request, 'backend/home/create_pillar.html')


def edit_core_pillar(request, pillar_id):
    pillar = get_object_or_404(CorePillar, id=pillar_id)
    if request.method == 'POST':
        errors = {}
        title = request.POST.get('title', '').strip()
        desc  = request.POST.get('description', '').strip()
        if not title: errors['title']       = ['Title is required.']
        if not desc:  errors['description'] = ['Description is required.']
        if errors:
            return JsonResponse({'success': False, 'message': 'Please fix the errors.', 'errors': errors}, status=400)
        # icon_class is not in the form — keep the existing value unchanged
        pillar.title       = title
        pillar.description = desc
        pillar.order       = int(request.POST.get('order') or 0)
        pillar.is_active   = request.POST.get('is_active') == 'true'
        pillar.save()
        return JsonResponse({'success': True, 'message': 'Pillar updated successfully!'})
    return render(request, 'backend/home/edit_pillar.html', {'pillar': pillar})


def delete_core_pillar(request, pillar_id):
    if request.method == 'POST':
        get_object_or_404(CorePillar, id=pillar_id).delete()
        return JsonResponse({'success': True, 'message': 'Pillar deleted.'})
    return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=400)


# ── Home Achievements ─────────────────────────────────────────────────────────

def list_home_achievements(request):
    achievements = HomeAchievement.objects.all()
    return render(request, 'backend/home/achievement_list.html', {'achievements': achievements})


_ACHIEVEMENT_ICONS = [
    'fas fa-trophy', 'fas fa-user-graduate', 'fas fa-star', 'fas fa-globe',
    'fas fa-medal', 'fas fa-award', 'fas fa-certificate', 'fas fa-ranking-star',
]

def create_home_achievement(request):
    if request.method == 'POST':
        errors = {}
        label = request.POST.get('label', '').strip()
        count = request.POST.get('count', '').strip()
        if not label: errors['label'] = ['Label is required.']
        if not count or not count.isdigit():
            errors['count'] = ['A valid whole number is required.']
        if errors:
            return JsonResponse({'success': False, 'message': 'Please fix the errors.', 'errors': errors}, status=400)
        icon = _ACHIEVEMENT_ICONS[HomeAchievement.objects.count() % len(_ACHIEVEMENT_ICONS)]
        HomeAchievement.objects.create(
            icon_class = icon,
            count      = int(count),
            suffix     = request.POST.get('suffix', '+').strip(),
            label      = label,
            order      = int(request.POST.get('order') or 0),
            is_active  = request.POST.get('is_active') == 'true',
        )
        return JsonResponse({'success': True, 'message': 'Achievement created successfully!'})
    return render(request, 'backend/home/create_achievement.html')


def edit_home_achievement(request, achievement_id):
    achievement = get_object_or_404(HomeAchievement, id=achievement_id)
    if request.method == 'POST':
        errors = {}
        label = request.POST.get('label', '').strip()
        count = request.POST.get('count', '').strip()
        if not label: errors['label'] = ['Label is required.']
        if not count or not count.isdigit():
            errors['count'] = ['A valid whole number is required.']
        if errors:
            return JsonResponse({'success': False, 'message': 'Please fix the errors.', 'errors': errors}, status=400)
        # icon_class is not in the form — keep existing value unchanged
        achievement.count      = int(count)
        achievement.suffix     = request.POST.get('suffix', '+').strip()
        achievement.label      = label
        achievement.order      = int(request.POST.get('order') or 0)
        achievement.is_active  = request.POST.get('is_active') == 'true'
        achievement.save()
        return JsonResponse({'success': True, 'message': 'Achievement updated successfully!'})
    return render(request, 'backend/home/edit_achievement.html', {'achievement': achievement})


def delete_home_achievement(request, achievement_id):
    if request.method == 'POST':
        get_object_or_404(HomeAchievement, id=achievement_id).delete()
        return JsonResponse({'success': True, 'message': 'Achievement deleted.'})
    return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=400)


# ─────────────────────────────────────────────────────────────────────────────
# CURRICULUM STAGES
# ─────────────────────────────────────────────────────────────────────────────

def list_curriculum_stages(request):
    stages = CurriculumStage.objects.all()
    return render(request, 'backend/curriculum/stage_list.html', {'stages': stages})


def create_curriculum_stage(request):
    if request.method == 'POST':
        errors = {}
        label   = request.POST.get('label', '').strip()
        heading = request.POST.get('heading', '').strip()
        desc    = request.POST.get('description', '').strip()
        if not label:   errors['label']       = ['Label is required.']
        if not heading: errors['heading']      = ['Heading is required.']
        if not desc:    errors['description']  = ['Description is required.']
        if errors:
            return JsonResponse({'success': False, 'message': 'Please fix the errors.', 'errors': errors}, status=400)

        icon = _CURRICULUM_ICONS[CurriculumStage.objects.count() % len(_CURRICULUM_ICONS)]
        stage = CurriculumStage(
            label       = label,
            age_group   = request.POST.get('age_group', '').strip(),
            icon_class  = icon,
            heading     = heading,
            description = desc,
            feature_1   = request.POST.get('feature_1', '').strip(),
            feature_2   = request.POST.get('feature_2', '').strip(),
            feature_3   = request.POST.get('feature_3', '').strip(),
            order       = int(request.POST.get('order') or 0),
            is_active   = request.POST.get('is_active') == 'true',
        )
        if 'image' in request.FILES:
            img = request.FILES['image']
            if img.content_type.startswith('image/'):
                stage.image = img
            else:
                return JsonResponse({'success': False, 'message': 'Uploaded file must be an image.', 'errors': {'image': ['Invalid file type.']}}, status=400)
        stage.save()
        return JsonResponse({'success': True, 'message': 'Curriculum stage created successfully!'})
    return render(request, 'backend/curriculum/create_stage.html')


def edit_curriculum_stage(request, stage_id):
    stage = get_object_or_404(CurriculumStage, id=stage_id)
    if request.method == 'POST':
        errors = {}
        label   = request.POST.get('label', '').strip()
        heading = request.POST.get('heading', '').strip()
        desc    = request.POST.get('description', '').strip()
        if not label:   errors['label']       = ['Label is required.']
        if not heading: errors['heading']      = ['Heading is required.']
        if not desc:    errors['description']  = ['Description is required.']
        if errors:
            return JsonResponse({'success': False, 'message': 'Please fix the errors.', 'errors': errors}, status=400)

        stage.label       = label
        stage.age_group   = request.POST.get('age_group', '').strip()
        stage.heading     = heading
        stage.description = desc
        stage.feature_1   = request.POST.get('feature_1', '').strip()
        stage.feature_2   = request.POST.get('feature_2', '').strip()
        stage.feature_3   = request.POST.get('feature_3', '').strip()
        stage.order       = int(request.POST.get('order') or 0)
        stage.is_active   = request.POST.get('is_active') == 'true'
        if 'image' in request.FILES:
            img = request.FILES['image']
            if img.content_type.startswith('image/'):
                stage.image = img
            else:
                return JsonResponse({'success': False, 'message': 'Uploaded file must be an image.'}, status=400)
        stage.save()
        return JsonResponse({'success': True, 'message': 'Curriculum stage updated successfully!'})
    return render(request, 'backend/curriculum/edit_stage.html', {'stage': stage})


def delete_curriculum_stage(request, stage_id):
    if request.method == 'POST':
        get_object_or_404(CurriculumStage, id=stage_id).delete()
        return JsonResponse({'success': True, 'message': 'Stage deleted.'})
    return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=400)


# ─────────────────────────────────────────────────────────────────────────────
# USER MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

from django.contrib.auth import get_user_model, update_session_auth_hash
from user_app.models import UserProfile

User = get_user_model()

# Allowed user types an admin can create/manage (no Root Admin via UI)
_MANAGEABLE_TYPES = [
    (1, 'Admin'),
    (2, 'Staff'),
    (3, 'Faculty'),
    (4, 'Student'),
]

_STATUS_CHOICES = [
    (1, 'Active'),
    (0, 'Inactive'),
    (2, 'Suspended'),
]


def list_users(request):
    users = User.objects.exclude(user_type=0).order_by('-created_at')
    return render(request, 'backend/users/user_list.html', {
        'users': users,
        'user_type_choices': _MANAGEABLE_TYPES,
    })


def create_user(request):
    if request.method == 'POST':
        errors = {}
        first_name   = request.POST.get('first_name',   '').strip()
        last_name    = request.POST.get('last_name',    '').strip()
        email        = request.POST.get('email',        '').strip()
        phone        = request.POST.get('phone_number', '').strip()
        password     = request.POST.get('password',     '')
        password2    = request.POST.get('password2',    '')
        user_type    = request.POST.get('user_type',    '4')
        user_status  = request.POST.get('user_status',  '1')

        if not first_name:
            errors['first_name'] = ['First name is required.']
        if not email:
            errors['email'] = ['Email is required.']
        elif User.objects.filter(email=email).exists():
            errors['email'] = ['A user with this email already exists.']
        if not phone:
            errors['phone_number'] = ['Phone number is required.']
        elif User.objects.filter(phone_number=phone).exists():
            errors['phone_number'] = ['A user with this phone number already exists.']
        if not password:
            errors['password'] = ['Password is required.']
        elif len(password) < 6:
            errors['password'] = ['Password must be at least 6 characters.']
        elif password != password2:
            errors['password2'] = ['Passwords do not match.']
        try:
            user_type = int(user_type)
            if user_type not in [t[0] for t in _MANAGEABLE_TYPES]:
                errors['user_type'] = ['Invalid user type.']
        except ValueError:
            errors['user_type'] = ['Invalid user type.']

        if errors:
            return JsonResponse({'success': False, 'message': 'Please fix the errors below.', 'errors': errors}, status=400)

        try:
            user = User.objects.create_user(
                email=email,
                phone_number=phone or None,
                password=password,
                first_name=first_name,
                last_name=last_name,
                user_type=user_type,
                user_status=int(user_status),
                is_staff=(user_type in (1, 2)),
            )
            return JsonResponse({'success': True, 'message': f'User "{user.get_display_name()}" created successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return render(request, 'backend/users/create_user.html', {
        'user_type_choices': _MANAGEABLE_TYPES,
        'status_choices':    _STATUS_CHOICES,
    })


def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user.user_type == 0:
        return JsonResponse({'success': False, 'message': 'Root Admin cannot be edited here.'}, status=403)

    if request.method == 'POST':
        errors = {}
        first_name  = request.POST.get('first_name',   '').strip()
        last_name   = request.POST.get('last_name',    '').strip()
        email       = request.POST.get('email',        '').strip()
        phone       = request.POST.get('phone_number', '').strip()
        password    = request.POST.get('password',     '')
        password2   = request.POST.get('password2',    '')
        user_type   = request.POST.get('user_type',    str(user.user_type))
        user_status = request.POST.get('user_status',  str(user.user_status))
        is_active   = request.POST.get('is_active') == 'true'

        if not first_name:
            errors['first_name'] = ['First name is required.']
        if not email:
            errors['email'] = ['Email is required.']
        elif User.objects.filter(email=email).exclude(id=user_id).exists():
            errors['email'] = ['Another user with this email already exists.']
        if not phone:
            errors['phone_number'] = ['Phone number is required.']
        elif User.objects.filter(phone_number=phone).exclude(id=user_id).exists():
            errors['phone_number'] = ['Another user with this phone number already exists.']
        if password:
            if len(password) < 6:
                errors['password'] = ['Password must be at least 6 characters.']
            elif password != password2:
                errors['password2'] = ['Passwords do not match.']
        try:
            user_type = int(user_type)
        except ValueError:
            errors['user_type'] = ['Invalid user type.']

        if errors:
            return JsonResponse({'success': False, 'message': 'Please fix the errors below.', 'errors': errors}, status=400)

        try:
            user.first_name  = first_name
            user.last_name   = last_name
            user.email       = email
            user.phone_number = phone or None
            user.user_type   = user_type
            user.user_status = int(user_status)
            user.is_active   = is_active
            user.is_staff    = (user_type in (1, 2))
            if password:
                user.set_password(password)
            user.save()
            return JsonResponse({'success': True, 'message': 'User updated successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return render(request, 'backend/users/edit_user.html', {
        'edit_user_obj':  user,
        'user_type_choices': _MANAGEABLE_TYPES,
        'status_choices':    _STATUS_CHOICES,
    })


def delete_user(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        if user.user_type == 0:
            return JsonResponse({'success': False, 'message': 'Root Admin cannot be deleted.'}, status=403)
        if user == request.user:
            return JsonResponse({'success': False, 'message': 'You cannot delete your own account.'}, status=400)
        name = user.get_display_name()
        user.delete()
        return JsonResponse({'success': True, 'message': f'User "{name}" deleted.'})
    return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=400)


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN PROFILE
# ─────────────────────────────────────────────────────────────────────────────

def admin_profile(request):
    user    = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        errors = {}
        first_name = request.POST.get('first_name', '').strip()
        email      = request.POST.get('email',      '').strip()
        phone      = request.POST.get('phone_number','').strip()
        last_name  = request.POST.get('last_name',  '').strip()
        address    = request.POST.get('address',    '').strip()

        # Mandatory field validation
        if not first_name:
            errors['first_name']   = ['First name is required.']
        if not email:
            errors['email']        = ['Email is required.']
        elif User.objects.filter(email=email).exclude(pk=user.pk).exists():
            errors['email']        = ['This email is already in use by another account.']
        if not phone:
            errors['phone_number'] = ['Phone number is required.']
        elif User.objects.filter(phone_number=phone).exclude(pk=user.pk).exists():
            errors['phone_number'] = ['This phone number is already in use.']

        # Password change (optional — only if fields supplied)
        old_password  = request.POST.get('old_password',  '')
        new_password  = request.POST.get('new_password',  '')
        new_password2 = request.POST.get('new_password2', '')
        change_pw = bool(old_password or new_password or new_password2)
        if change_pw:
            if not user.check_password(old_password):
                errors['old_password'] = ['Current password is incorrect.']
            elif len(new_password) < 6:
                errors['new_password'] = ['New password must be at least 6 characters.']
            elif new_password != new_password2:
                errors['new_password2'] = ['Passwords do not match.']

        if errors:
            return JsonResponse({'success': False, 'message': 'Please fix the errors below.', 'errors': errors}, status=400)

        try:
            user.first_name   = first_name
            user.last_name    = last_name
            user.email        = email
            user.phone_number = phone or None
            if change_pw:
                user.set_password(new_password)
            user.save()

            profile.address = address
            if 'profile_picture' in request.FILES:
                img = request.FILES['profile_picture']
                if img.content_type.startswith('image/'):
                    profile.profile_picture = img
                else:
                    return JsonResponse({'success': False, 'message': 'Profile picture must be an image file.'})
            profile.save()

            if change_pw:
                update_session_auth_hash(request, user)

            return JsonResponse({'success': True, 'message': 'Profile updated successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return render(request, 'backend/users/profile.html', {
        'profile_user': user,
        'profile':      profile,
    })