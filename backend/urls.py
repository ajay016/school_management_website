from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.decorators import login_required
from . import views

# Shorthand — only admin/staff users should reach these pages
lr = login_required  # applied to every HTML-page-rendering view below


urlpatterns = [
    # ── Dashboard ──────────────────────────────────────────────────────────
    path('', lr(views.admin_dashboard), name='admin_dashboard'),

    # ── Sliders ────────────────────────────────────────────────────────────
    path('sliders/',                  lr(views.list_home_sliders),   name='list_home_sliders'),
    path('sliders/create/',           lr(views.create_home_slider),  name='create_home_slider'),
    path('sliders/delete/<int:pk>/',  views.delete_home_slider,      name='delete_home_slider'),
    path('sliders/edit/<int:pk>/',    lr(views.edit_home_slider),    name='edit_home_slider'),

    # ── Navbar Menus ───────────────────────────────────────────────────────
    path('menus/create/',             lr(views.create_menu),  name='create_menu'),
    path('menus/',                    lr(views.list_menus),   name='list_menus'),
    path('menus/<int:id>/edit/',      lr(views.edit_menu),    name='edit_menu'),
    path('menus/<int:id>/delete/',    views.delete_menu,      name='delete_menu'),

    # ── SubMenu AJAX endpoints (data — no page render) ─────────────────────
    path('menus/<int:menu_id>/submenu/create/', views.create_submenu, name='create_submenu'),
    path('submenus/<int:id>/get/',              views.get_submenu,    name='get_submenu'),
    path('submenus/<int:id>/update/',           views.update_submenu, name='update_submenu'),
    path('submenus/<int:id>/delete/',           views.delete_submenu, name='delete_submenu'),

    # ── Page Layouts ───────────────────────────────────────────────────────
    path('layouts/layout-1/',                               lr(views.list_layout1),          name='list_layout1'),
    path('layouts/layout-1/create/',                        lr(views.create_page_section),   name='create_page_section'),
    path('dashboard/layouts/layout-1/edit/<int:id>/',       lr(views.edit_layout1_section),  name='edit_layout1_section'),
    path('layouts/layout-1/delete/<int:section_id>/',       views.delete_layout1_section,    name='delete_layout1_section'),

    path('cms/layout2/create/',                                lr(views.create_page_photo),          name='create_page_photo'),
    path('cms/layout2/',                                       lr(views.list_page_photo),            name='list_page_photo'),
    path('cms/layout2/edit-gallery/<int:submenu_id>/',         lr(views.edit_layout2_gallery),       name='edit_layout2_gallery'),
    path('cms/layout2/edit-gallery-menu/<int:menu_id>/',       lr(views.edit_layout2_gallery_menu),  name='edit_layout2_gallery_menu'),
    path('cms/layout2/delete-photo/<int:photo_id>/',           views.delete_single_photo,            name='delete_single_photo'),
    path('cms/layout2/delete-gallery/<int:submenu_id>/',       views.delete_gallery,                 name='delete_gallery'),
    path('cms/layout2/delete-gallery-menu/<int:menu_id>/',     views.delete_gallery_menu,            name='delete_gallery_menu'),

    path('cms/layout3/create/',                                lr(views.create_page_rich_text),          name='create_page_rich_text'),
    path('cms/layout3/',                                       lr(views.list_layout3_rich_text),         name='list_layout3_rich_text'),
    path('cms/layout3/delete-all/<int:submenu_id>/',           views.delete_all_layout3_blocks,          name='delete_all_layout3_blocks'),
    path('cms/layout3/delete-all-menu/<int:menu_id>/',         views.delete_all_layout3_blocks_menu,     name='delete_all_layout3_blocks_menu'),
    path('cms/layout3/edit/<int:submenu_id>/',                 lr(views.edit_layout3_rich_text),         name='edit_layout3_rich_text'),
    path('cms/layout3/edit-menu/<int:menu_id>/',               lr(views.edit_layout3_rich_text_menu),    name='edit_layout3_rich_text_menu'),

    # ── Notices ────────────────────────────────────────────────────────────
    path('cms/notices/create/',           lr(views.create_notice), name='create_notice'),
    path('cms/notices/',                  lr(views.notice_list),   name='notice_list'),
    path('cms/notices/delete/<int:id>/',  views.delete_notice,     name='delete_notice'),
    path('cms/notices/edit/<int:id>/',    lr(views.edit_notice),   name='edit_notice'),

    # ── Events ─────────────────────────────────────────────────────────────
    path('events/create/',                    lr(views.create_event), name='create_event'),
    path('events/',                           lr(views.event_list),   name='event_list'),
    path('events/<int:event_id>/edit/',       lr(views.edit_event),   name='edit_event'),
    path('events/<int:event_id>/delete/',     views.delete_event,     name='delete_event'),

    # ── Gallery ────────────────────────────────────────────────────────────
    path('gallery/create/',                       lr(views.create_album), name='create_album'),
    path('gallery/',                              lr(views.album_list),   name='album_list'),
    path('gallery/<int:album_id>/edit/',          lr(views.edit_album),   name='edit_album'),
    path('gallery/<int:album_id>/delete/',        views.delete_album,     name='delete_album'),
    path('gallery/photo/<int:photo_id>/delete/',  views.delete_photo,     name='delete_photo'),

    # ── Contact & Logo ─────────────────────────────────────────────────────
    path('contact/', lr(views.edit_contact), name='edit_contact'),

    # ── Facilities ─────────────────────────────────────────────────────────
    path('facilities/',                          lr(views.list_facilities),  name='list_facilities'),
    path('facilities/create/',                   lr(views.create_facility),  name='create_facility'),
    path('facilities/edit/<int:id>/',            lr(views.edit_facility),    name='edit_facility'),
    path('facilities/delete/<int:facility_id>/', views.delete_facility,      name='delete_facility'),

    # ── Home Page Sections ─────────────────────────────────────────────────
    path('home/stats/',  lr(views.edit_hero_stats),  name='edit_hero_stats'),
    path('home/about/',  lr(views.edit_home_about),  name='edit_home_about'),

    path('home/pillars/',                         lr(views.list_core_pillars),    name='list_core_pillars'),
    path('home/pillars/create/',                  lr(views.create_core_pillar),   name='create_core_pillar'),
    path('home/pillars/<int:pillar_id>/edit/',    lr(views.edit_core_pillar),     name='edit_core_pillar'),
    path('home/pillars/<int:pillar_id>/delete/',  views.delete_core_pillar,       name='delete_core_pillar'),

    path('home/achievements/',                              lr(views.list_home_achievements),    name='list_home_achievements'),
    path('home/achievements/create/',                       lr(views.create_home_achievement),   name='create_home_achievement'),
    path('home/achievements/<int:achievement_id>/edit/',    lr(views.edit_home_achievement),     name='edit_home_achievement'),
    path('home/achievements/<int:achievement_id>/delete/',  views.delete_home_achievement,       name='delete_home_achievement'),

    # ── Curriculum Stages ──────────────────────────────────────────────────
    path('curriculum/',                            lr(views.list_curriculum_stages),  name='list_curriculum_stages'),
    path('curriculum/create/',                     lr(views.create_curriculum_stage), name='create_curriculum_stage'),
    path('curriculum/<int:stage_id>/edit/',        lr(views.edit_curriculum_stage),   name='edit_curriculum_stage'),
    path('curriculum/<int:stage_id>/delete/',      views.delete_curriculum_stage,     name='delete_curriculum_stage'),

    # ── User Management ────────────────────────────────────────────────────
    path('users/',                         lr(views.list_users),   name='list_users'),
    path('users/create/',                  lr(views.create_user),  name='create_user'),
    path('users/<int:user_id>/edit/',      lr(views.edit_user),    name='edit_user'),
    path('users/<int:user_id>/delete/',    views.delete_user,      name='delete_user'),

    # ── Admin Profile ──────────────────────────────────────────────────────
    path('profile/', lr(views.admin_profile), name='admin_profile'),
]
