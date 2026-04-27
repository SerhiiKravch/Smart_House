from django.db import models


class AutomationRule(models.Model):
    name = models.CharField(max_length=64, default="default")
    device = models.ForeignKey(
        "devices.Device",
        on_delete=models.CASCADE,
        related_name="automation_rules",
    )
    is_enabled = models.BooleanField(default=True)

    night_start_hour = models.PositiveSmallIntegerField(default=23)
    night_end_hour = models.PositiveSmallIntegerField(default=7)

    min_battery_soc_night = models.FloatField(default=50.0)
    min_wire_power_night = models.FloatField(default=0.0)
    min_generation_power_day = models.FloatField(default=1200.0)

    check_interval_seconds = models.PositiveIntegerField(default=300)
    priority = models.PositiveSmallIntegerField(default=100, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["priority", "id"]
        indexes = [
            models.Index(fields=["is_enabled", "priority"]),
        ]

    def __str__(self):
        return f"{self.name} -> {self.device.entity_id}"


class AutomationDecisionLog(models.Model):
    ACTION_TURN_ON = "turn_on"
    ACTION_TURN_OFF = "turn_off"
    ACTION_NO_CHANGE = "no_change"
    ACTION_SKIP = "skip"

    ACTION_CHOICES = [
        (ACTION_TURN_ON, "Turn On"),
        (ACTION_TURN_OFF, "Turn Off"),
        (ACTION_NO_CHANGE, "No Change"),
        (ACTION_SKIP, "Skip"),
    ]

    decided_at = models.DateTimeField(auto_now_add=True, db_index=True)
    rule = models.ForeignKey(
        AutomationRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="decision_logs",
    )
    device = models.ForeignKey(
        "devices.Device",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="decision_logs",
    )
    action = models.CharField(max_length=16, choices=ACTION_CHOICES)
    should_turn_on = models.BooleanField()
    mode = models.CharField(max_length=16, blank=True)
    reason = models.TextField()
    previous_state = models.CharField(max_length=16, blank=True)
    resulting_state = models.CharField(max_length=16, blank=True)

    battery_soc = models.FloatField(null=True, blank=True)
    generation_power = models.FloatField(null=True, blank=True)
    wire_power = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ["-decided_at"]
        indexes = [
            models.Index(fields=["-decided_at"]),
        ]

    def __str__(self):
        return f"{self.decided_at:%Y-%m-%d %H:%M:%S} {self.action}"
