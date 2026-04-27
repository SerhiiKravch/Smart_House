from apps.devices.models import Device
from apps.integrations.dto import SocketState
from apps.integrations.home_assistant import get_ha_client


async def fetch_live_socket_state(entity_id: str) -> SocketState | None:
    client = get_ha_client()
    await client.connect()
    try:
        state_data = await client.get_state(entity_id)
        if state_data is None:
            return None
        return SocketState(
            entity_id=entity_id,
            state=state_data.get("state"),
        )
    finally:
        await client.close()


async def refresh_device_state_from_ha(device: Device) -> SocketState | None:
    return await fetch_live_socket_state(device.entity_id)
