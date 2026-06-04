from django.contrib import admin
from .models import *














@admin.register(HomeSlider)
class HomeSliderAdmin(admin.ModelAdmin):
    list_display = ('heading', 'greeting_badge', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('heading', 'greeting_badge', 'short_description')
    
    fieldsets = (
        ('Images', {
            'fields': ('slider_image', 'hero_image')
        }),
        ('Text Content', {
            'fields': ('greeting_badge', 'heading', 'short_description')
        }),
        ('Call to Action (Button)', {
            'fields': ('button_label', 'button_link')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )