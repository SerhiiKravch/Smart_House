from datetime import datetime
import logging
from zoneinfo import ZoneInfo

from asgiref.sync import sync_to_async
from django.db.models import QuerySet

from apps.automation.models import AutomationDecisionLog, AutomationRule
from apps.automation.rules import (
    is_night_time,
    should_turn_on_at_day,
    should_turn_on_at_night,
)
from apps.devices.models import Device
from apps.integrations import solar_api

logger = logging.getLogger(__name__)


@sync_to_async
def _get_enabled_rules() -> list[AutomationRule]:
    queryset: QuerySet[AutomationRule] = (
        AutomationRule.objects
        .filter(is_enabled=True, device__is_active=True)
        .select_related("device")
        .order_by("priority", "id")
    )
    return list(queryset)


@sync_to_async
def _create_decision_log(**kwargs):
    AutomationDecisionLog.objects.create(**kwargs)


def _build_decision(rule: AutomationRule, hour: int, battery_data):
    is_night = is_night_time(hour, rule.night_start_hour, rule.night_end_hour)
    battery_soc = battery_data.battery_soc
    generation_power = battery_data.generation_power
    wire_power = battery_data.wire_power

    if is_night:
        should_turn_on = should_turn_on_at_night(
            battery_soc=battery_soc,
            wire_power=wire_power,
            min_battery_soc_night=rule.min_battery_soc_night,
            min_wire_power_night=rule.min_wire_power_night,
        )
        mode = "night"
        reason = (
            f"night: battery_soc={battery_soc}, wire_power={wire_power}, "
            f"thresholds=({rule.min_battery_soc_night}, {rule.min_wire_power_night})"
        )
    else:
        should_turn_on = should_turn_on_at_day(
            generation_power=generation_power,
            min_generation_power_day=rule.min_generation_power_day,
        )
        mode = "day"
        reason = (
            f"day: generation_power={generation_power}, "
            f"threshold={rule.min_generation_power_day}"
        )

    return should_turn_on, mode, reason


async def _apply_device_rule(client, rule: AutomationRule, battery_data, hour: int):
    device: Device = rule.device

    if device.device_type != Device.TYPE_SWITCH:
        logger.warning(
            "Skipping rule=%s device=%s: unsupported device_type=%s",
            rule.id,
            device.entity_id,
            device.device_type,
        )
        await _create_decision_log(
            rule=rule,
            device=device,
            action=AutomationDecisionLog.ACTION_SKIP,
            should_turn_on=False,
            mode="unsupported",
            reason=f"Unsupported device type: {device.device_type}",
        )
        return

    should_turn_on, mode, reason = _build_decision(rule, hour, battery_data)
    current_state_data = await client.get_state(device.entity_id)

    if current_state_data is None:
        logger.warning(
            "Skipping rule=%s device=%s: current state unavailable",
            rule.id,
            device.entity_id,
        )
        await _create_decision_log(
            rule=rule,
            device=device,
            action=AutomationDecisionLog.ACTION_SKIP,
            should_turn_on=should_turn_on,
            mode=mode,
            reason=f"{reason}; current state is unavailable",
            battery_soc=battery_data.battery_soc,
            generation_power=battery_data.generation_power,
            wire_power=battery_data.wire_power,
        )
        return

    current_state = current_state_data.get("state", "")
    action = AutomationDecisionLog.ACTION_NO_CHANGE
    resulting_state = current_state

    if should_turn_on and current_state != "on":
        await client.turn_on(device.entity_id)
        action = AutomationDecisionLog.ACTION_TURN_ON
        resulting_state = "on"
        logger.info(
            "Decision turn_on rule=%s device=%s prev=%s mode=%s",
            rule.id,
            device.entity_id,
            current_state,
            mode,
        )
    elif not should_turn_on and current_state != "off":
        await client.turn_off(device.entity_id)
        action = AutomationDecisionLog.ACTION_TURN_OFF
        resulting_state = "off"
        logger.info(
            "Decision turn_off rule=%s device=%s prev=%s mode=%s",
            rule.id,
            device.entity_id,
            current_state,
            mode,
        )
    else:
        logger.info(
            "Decision no_change rule=%s device=%s state=%s mode=%s",
            rule.id,
            device.entity_id,
            current_state,
            mode,
        )

    await _create_decision_log(
        rule=rule,
        device=device,
        action=action,
        should_turn_on=should_turn_on,
        mode=mode,
        reason=reason,
        previous_state=current_state,
        resulting_state=resulting_state,
        battery_soc=battery_data.battery_soc,
        generation_power=battery_data.generation_power,
        wire_power=battery_data.wire_power,
    )


async def run_automation_cycle(client) -> int:
    rules = await _get_enabled_rules()
    if not rules:
        logger.info("Automation cycle: no enabled rules, sleeping 300s")
        return 300

    battery_data = await solar_api.get_selected_data()
    if not battery_data:
        logger.warning("Automation cycle: solar data unavailable")
        return min(rule.check_interval_seconds for rule in rules)

    kyiv_now = datetime.now(ZoneInfo("Europe/Kyiv"))
    logger.info(
        "Automation cycle started: rules=%s hour=%s battery_soc=%s generation=%s wire=%s",
        len(rules),
        kyiv_now.hour,
        battery_data.battery_soc,
        battery_data.generation_power,
        battery_data.wire_power,
    )
    for rule in rules:
        await _apply_device_rule(
            client=client,
            rule=rule,
            battery_data=battery_data,
            hour=kyiv_now.hour,
        )

    next_interval = min(rule.check_interval_seconds for rule in rules)
    logger.info("Automation cycle finished, next check in %ss", next_interval)
    return next_interval
