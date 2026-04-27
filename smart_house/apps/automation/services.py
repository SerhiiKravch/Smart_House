from datetime import datetime
from zoneinfo import ZoneInfo

from apps.integrations import solar_api


async def control_socket(client, entity_id):
    kyiv_now = datetime.now(ZoneInfo("Europe/Kyiv"))
    is_night = kyiv_now.hour >= 23 or kyiv_now.hour <= 7

    battery_data = await solar_api.get_selected_data()
    if not battery_data:
        return 600

    battery_soc = battery_data.battery_soc
    generation_power = battery_data.generation_power
    wire_power = battery_data.wire_power

    is_battery_ok = battery_soc is not None and battery_soc > 50
    is_generation_ok = generation_power is not None and generation_power > 1200
    is_wire_ok = wire_power is not None and wire_power > 0

    if is_night:
        should_turn_on = is_battery_ok and is_wire_ok
        interval = 600
    else:
        should_turn_on = is_generation_ok
        interval = 600

    current_state_data = await client.get_state(entity_id)
    if current_state_data is None:
        return interval

    current_state = current_state_data.get("state")

    if should_turn_on and current_state != "on":
        await client.turn_on(entity_id)
    elif not should_turn_on and current_state != "off":
        await client.turn_off(entity_id)

    return interval
