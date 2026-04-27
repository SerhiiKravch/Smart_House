from django.db import models


class Device(models.Model):
    TYPE_SWITCH = "switch"
    TYPE_LIGHT = "light"
    TYPE_CLIMATE = "climate"
    TYPE_SENSOR = "sensor"

    TYPE_CHOICES = [
        (TYPE_SWITCH, "Switch"),
        (TYPE_LIGHT, "Light"),
        (TYPE_CLIMATE, "Climate"),
        (TYPE_SENSOR, "Sensor"),
    ]

    name = models.CharField(max_length=120)
    entity_id = models.CharField(max_length=128, unique=True)
    device_type = models.CharField(
        max_length=32,
        choices=TYPE_CHOICES,
        default=TYPE_SWITCH,
        db_index=True,
    )
    room = models.CharField(max_length=64, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    capabilities = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.entity_id})"
