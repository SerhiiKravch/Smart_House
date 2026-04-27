def is_night_time(hour: int) -> bool:
    return hour >= 23 or hour <= 7


def should_turn_on_at_night(battery_soc, wire_power) -> bool:
    return (
        battery_soc is not None and battery_soc > 50 and
        wire_power is not None and wire_power > 0
    )


def should_turn_on_at_day(generation_power) -> bool:
    return generation_power is not None and generation_power > 1200