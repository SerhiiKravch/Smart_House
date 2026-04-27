from django.http import JsonResponse
from django.shortcuts import render

from .services import get_dashboard_context


def status_view(request):
    context = get_dashboard_context(request.GET.get("device_id"), live_ha=True)
    return render(request, "dashboard/status.html", context)


def summary_api_view(request):
    live_ha = request.GET.get("live_ha") == "1"
    context = get_dashboard_context(request.GET.get("device_id"), live_ha=live_ha)
    socket_state = context.get("socket_state")
    decision = context.get("latest_decision")
    socket_state_value = None
    if isinstance(socket_state, dict):
        socket_state_value = socket_state.get("state")
    elif socket_state is not None:
        socket_state_value = getattr(socket_state, "state", None)

    data = {
        "device": (
            {
                "id": context["selected_device"].id,
                "name": context["selected_device"].name,
                "entity_id": context["selected_device"].entity_id,
            }
            if context.get("selected_device") else None
        ),
        "socket_state": (
            {
                "state": socket_state_value,
                "source": context.get("socket_state_source"),
            }
        ),
        "solar": (
            {
                "battery_soc": context["solar_data"].battery_soc,
                "generation_power": context["solar_data"].generation_power,
                "wire_power": context["solar_data"].wire_power,
            }
            if context.get("solar_data") else None
        ),
        "weather": context.get("weather_data"),
        "health": context.get("dependency_health"),
        "latest_decision": (
            {
                "action": decision.action,
                "mode": decision.mode,
                "previous_state": decision.previous_state,
                "resulting_state": decision.resulting_state,
                "reason": decision.reason,
                "decided_at": decision.decided_at.isoformat(),
            }
            if decision else None
        ),
    }
    return JsonResponse(data)
