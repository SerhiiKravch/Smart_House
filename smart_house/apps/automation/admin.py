from django.contrib import admin

from .models import AutomationDecisionLog, AutomationRule


@admin.register(AutomationRule)
class AutomationRuleAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "device",
        "is_enabled",
        "priority",
        "night_start_hour",
        "night_end_hour",
        "check_interval_seconds",
    )
    list_filter = ("is_enabled", "priority", "device__device_type")
    search_fields = ("name", "device__name", "device__entity_id")


@admin.register(AutomationDecisionLog)
class AutomationDecisionLogAdmin(admin.ModelAdmin):
    list_display = (
        "decided_at",
        "device",
        "rule",
        "action",
        "mode",
        "previous_state",
        "resulting_state",
    )
    list_filter = ("action", "mode")
    search_fields = ("device__name", "device__entity_id", "reason")
    readonly_fields = (
        "decided_at",
        "rule",
        "device",
        "action",
        "should_turn_on",
        "mode",
        "reason",
        "previous_state",
        "resulting_state",
        "battery_soc",
        "generation_power",
        "wire_power",
    )
