from django.contrib import admin
from django.urls import path, include
from . import views











urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    
    # Slider
    path('sliders/', views.list_home_sliders, name='list_home_sliders'),
    path('sliders/create/', views.create_home_slider, name='create_home_slider'),
    path('sliders/delete/<int:pk>/', views.delete_home_slider, name='delete_home_slider'),
    path('sliders/edit/<int:pk>/', views.edit_home_slider, name='edit_home_slider'),
    
    # Navbar Menus
    path('menus/create/', views.create_menu, name='create_menu'),
    path('menus/', views.list_menus, name='list_menus'),
    path('menus/<int:id>/edit/', views.edit_menu, name='edit_menu'),
    path('menus/<int:id>/delete/', views.delete_menu, name='delete_menu'),
    
    # SubMenu AJAX Endpoints
    path('menus/<int:menu_id>/submenu/create/', views.create_submenu, name='create_submenu'),
    path('submenus/<int:id>/get/', views.get_submenu, name='get_submenu'),
    path('submenus/<int:id>/update/', views.update_submenu, name='update_submenu'),
    path('submenus/<int:id>/delete/', views.delete_submenu, name='delete_submenu'),
    
    # Page Layouts
    path('layouts/layout-1/', views.list_layout1, name='list_layout1'),
    path('layouts/layout-1/create/', views.create_page_section, name='create_page_section'),
    path('dashboard/layouts/layout-1/edit/<int:id>/', views.edit_layout1_section, name='edit_layout1_section'),
    path('layouts/layout-1/delete/<int:section_id>/', views.delete_layout1_section, name='delete_layout1_section'),
    
    path('cms/layout2/create/', views.create_page_photo, name='create_page_photo'),
    path('cms/layout2/', views.list_page_photo, name='list_page_photo'),
    path('cms/layout2/edit-gallery/<int:submenu_id>/', views.edit_layout2_gallery, name='edit_layout2_gallery'),
    path('cms/layout2/delete-photo/<int:photo_id>/', views.delete_single_photo, name='delete_single_photo'),
    path('cms/layout2/delete-gallery/<int:submenu_id>/', views.delete_gallery, name='delete_gallery'),
    
    path('cms/layout3/create/', views.create_page_rich_text, name='create_page_rich_text'),
    path('cms/layout3/', views.list_layout3_rich_text, name='list_layout3_rich_text'),
    path('cms/layout3/delete-all/<int:submenu_id>/', views.delete_all_layout3_blocks, name='delete_all_layout3_blocks'),
    path('cms/layout3/edit/<int:submenu_id>/', views.edit_layout3_rich_text, name='edit_layout3_rich_text'),
    
    # Notice
    path('cms/notices/create/', views.create_notice, name='create_notice'),
    path('cms/notices/', views.notice_list, name='notice_list'),
    path('cms/notices/delete/<int:id>/', views.delete_notice, name='delete_notice'),
    path('cms/notices/edit/<int:id>/', views.edit_notice, name='edit_notice'),
    
    
    # ── Events ──────────────────────────────────────────────
    path('events/create/', views.create_event, name='create_event'),
    path('events/', views.event_list, name='event_list'),
    path('events/<int:event_id>/edit/', views.edit_event, name='edit_event'),
    path('events/<int:event_id>/delete/', views.delete_event, name='delete_event'),
 
    # ── Gallery Albums ───────────────────────────────────────
    path('gallery/create/', views.create_album, name='create_album'),
    path('gallery/', views.album_list, name='album_list'),
    path('gallery/<int:album_id>/edit/', views.edit_album, name='edit_album'),
    path('gallery/<int:album_id>/delete/', views.delete_album, name='delete_album'),
    path('gallery/photo/<int:photo_id>/delete/', views.delete_photo, name='delete_photo'),
    
    # Contact
    path('contact/', views.edit_contact, name='edit_contact'),
    
    # Facilities
    path('facilities/', views.list_facilities, name='list_facilities'),
    path('facilities/create/', views.create_facility, name='create_facility'),
    path('facilities/edit/<int:id>/', views.edit_facility, name='edit_facility'),
    path('facilities/delete/<int:facility_id>/', views.delete_facility, name='delete_facility'),

    # Home page sections
    path('home/stats/', views.edit_hero_stats, name='edit_hero_stats'),
    path('home/about/', views.edit_home_about, name='edit_home_about'),

    path('home/pillars/', views.list_core_pillars, name='list_core_pillars'),
    path('home/pillars/create/', views.create_core_pillar, name='create_core_pillar'),
    path('home/pillars/<int:pillar_id>/edit/', views.edit_core_pillar, name='edit_core_pillar'),
    path('home/pillars/<int:pillar_id>/delete/', views.delete_core_pillar, name='delete_core_pillar'),

    path('home/achievements/', views.list_home_achievements, name='list_home_achievements'),
    path('home/achievements/create/', views.create_home_achievement, name='create_home_achievement'),
    path('home/achievements/<int:achievement_id>/edit/', views.edit_home_achievement, name='edit_home_achievement'),
    path('home/achievements/<int:achievement_id>/delete/', views.delete_home_achievement, name='delete_home_achievement'),

    # Curriculum Stages
    path('curriculum/', views.list_curriculum_stages, name='list_curriculum_stages'),
    path('curriculum/create/', views.create_curriculum_stage, name='create_curriculum_stage'),
    path('curriculum/<int:stage_id>/edit/', views.edit_curriculum_stage, name='edit_curriculum_stage'),
    path('curriculum/<int:stage_id>/delete/', views.delete_curriculum_stage, name='delete_curriculum_stage'),
]