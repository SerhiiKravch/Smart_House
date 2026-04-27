from asgiref.sync import async_to_sync
from django.utils import timezone

from apps.automation.models import AutomationDecisionLog, AutomationRule
from apps.devices.models import Device
from apps.integrations import solar_api, weather_api
from apps.integrations.services import refresh_device_state_from_ha


def _health(status: str, message: str):
    return {
        "status": status,
        "message": message,
        "checked_at": timezone.now(),
    }


def _format_ha_error(exc: Exception) -> str:
    message = str(exc)
    if "nodename nor servname provided" in message:
        return (
            "HA host cannot be resolved. "
            "Check HA_WS_URL and prefer LAN IP instead of .local hostname."
        )
    return f"HA error: {message}"


def _pick_device(device_id: str | None):
    base_qs = Device.objects.filter(is_active=True, device_type=Device.TYPE_SWITCH)
    if not base_qs.exists():
        return None, list(base_qs)

    if device_id:
        selected = base_qs.filter(id=device_id).first()
        if selected:
            return selected, list(base_qs)

    return base_qs.first(), list(base_qs)


def get_dashboard_context(device_id: str | None = None, live_ha: bool = True):
    selected_device, switch_devices = _pick_device(device_id)

    context = {
        "now": timezone.now(),
        "devices": switch_devices,
        "selected_device": selected_device,
        "socket_state": None,
        "socket_state_source": "unavailable",
        "latest_decision": None,
        "active_rule": None,
        "solar_data": None,
        "weather_data": None,
        "dependency_health": {
            "ha": _health("unknown", "Not checked"),
            "solar": _health("unknown", "Not checked"),
            "weather": _health("unknown", "Not checked"),
        },
    }

    if not selected_device:
        context["empty_state"] = (
            "No active switch devices found. Add a switch device in admin first."
        )
        return context

    latest_decision = (
        AutomationDecisionLog.objects
        .filter(device=selected_device)
        .select_related("rule")
        .first()
    )
    active_rule = (
        AutomationRule.objects
        .filter(device=selected_device, is_enabled=True)
        .order_by("priority", "id")
        .first()
    )
    context["latest_decision"] = latest_decision
    context["active_rule"] = active_rule

    if live_ha:
        try:
            socket_state = async_to_sync(refresh_device_state_from_ha)(selected_device)
            context["socket_state"] = socket_state
            context["socket_state_source"] = "ha_live"
            if socket_state:
                context["dependency_health"]["ha"] = _health("healthy", "Live check succeeded")
            else:
                context["dependency_health"]["ha"] = _health("degraded", "Device state not found in HA")
        except Exception as exc:
            context["dependency_health"]["ha"] = _health("down", _format_ha_error(exc))
            if latest_decision:
                context["socket_state"] = {
                    "entity_id": selected_device.entity_id,
                    "state": latest_decision.resulting_state or "unknown",
                }
                context["socket_state_source"] = "decision_log"
    else:
        context["dependency_health"]["ha"] = _health("unknown", "Live check skipped")
        if latest_decision:
            context["socket_state"] = {
                "entity_id": selected_device.entity_id,
                "state": latest_decision.resulting_state or "unknown",
            }
            context["socket_state_source"] = "decision_log"

    try:
        solar_data = async_to_sync(solar_api.get_selected_data)()
        context["solar_data"] = solar_data
        context["dependency_health"]["solar"] = _health("healthy", "Live check succeeded")
    except Exception as exc:
        context["dependency_health"]["solar"] = _health("down", f"Solar API error: {exc}")

    try:
        weather_raw = async_to_sync(weather_api.get_current_weather)()
        current_weather = weather_raw.get("current", {})
        weather_code = current_weather.get("weather_code")
        context["weather_data"] = {
            "weather_code": weather_code,
            "weather_description": weather_api.get_weather_description(weather_code)
            if weather_code is not None else "Unknown",
            "temperature": current_weather.get("temperature_2m"),
            "cloud_cover": current_weather.get("cloud_cover"),
            "wind_speed": current_weather.get("wind_speed_10m"),
        }
        context["dependency_health"]["weather"] = _health("healthy", "Live check succeeded")
    except Exception as exc:
        context["dependency_health"]["weather"] = _health("down", f"Weather API error: {exc}")

    return context
