from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    # Dynamic CMS pages — layout_1 / layout_2 / layout_3
    path('page/<slug:menu_slug>/<slug:submenu_slug>/', views.dynamic_page, name='dynamic_page'),

    # Gallery
    path('galleries/', views.galleries, name='galleries'),

    # Special pages
    path('notices/', views.notices, name='notices'),
    path('events/', views.events, name='events'),
    path('contact/', views.contact, name='contact'),

    # Individual Facility detail pages (/facility/<slug>/)
    path('facility/<slug:slug>/', views.facility_detail, name='facility_detail'),

    # Individual Curriculum Stage detail pages (/curriculum/<slug>/)
    path('curriculum/<slug:slug>/', views.curriculum_detail, name='curriculum_detail'),
]

# NOTE: Static pages like our-school, mission, admission-info, national-curriculum,
# british-curriculum, library-facilities, science-labs, school-rules, dress-code
# have been removed. The admin now creates these as submenus with page=layout_1
# (or layout_2/3), and they are served through the dynamic_page view above.
# Example admin setup:
#   Menu "About Us" → SubMenu "Our School" (page=layout_1) → /page/about-us/our-school/
#   Menu "Facilities" → SubMenu "Library"  (page=layout_1) → /page/facilities/library/
