from django.contrib import admin

from .models import Device


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("name", "entity_id", "device_type", "room", "is_active")
    list_filter = ("device_type", "is_active", "room")
    search_fields = ("name", "entity_id")
