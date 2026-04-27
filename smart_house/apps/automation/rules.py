def is_night_time(hour: int, start_hour: int, end_hour: int) -> bool:
    if start_hour == end_hour:
        return True

    if start_hour < end_hour:
        return start_hour <= hour < end_hour

    return hour >= start_hour or hour < end_hour


def should_turn_on_at_night(
    battery_soc,
    wire_power,
    min_battery_soc_night: float,
    min_wire_power_night: float,
) -> bool:
    return (
        battery_soc is not None
        and battery_soc > min_battery_soc_night
        and wire_power is not None
        and wire_power > min_wire_power_night
    )


def should_turn_on_at_day(generation_power, min_generation_power_day: float) -> bool:
    return (
        generation_power is not None
        and generation_power > min_generation_power_day
    )
