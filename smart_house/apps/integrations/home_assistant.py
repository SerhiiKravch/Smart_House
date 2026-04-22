import asyncio
import json

import websockets
from django.conf import settings

from .exceptions import HomeAssistantError


class HAWebSocketClient:
    def __init__(self, ws_url: str, token: str):
        self.ws_url = ws_url
        self.token = token
        self.websocket = None
        self.msg_id = 1
        self.pending = {}
        self.reader_task = None

    async def connect(self):
        try:
            self.websocket = await websockets.connect(self.ws_url)

            hello_msg = json.loads(await self.websocket.recv())
            if hello_msg.get("type") != "auth_required":
                raise HomeAssistantError(f"Unexpected hello message: {hello_msg}")

            await self.websocket.send(json.dumps({
                "type": "auth",
                "access_token": self.token
            }))

            auth_msg = json.loads(await self.websocket.recv())
            if auth_msg.get("type") != "auth_ok":
                raise HomeAssistantError(f"Auth failed: {auth_msg}")

            self.reader_task = asyncio.create_task(self._reader())

        except Exception as e:
            raise HomeAssistantError(f"Failed to connect to Home Assistant: {e}") from e

    async def _reader(self):
        try:
            while True:
                raw = await self.websocket.recv()
                data = json.loads(raw)

                if "id" in data and data["id"] in self.pending:
                    future = self.pending.pop(data["id"])
                    if not future.done():
                        future.set_result(data)
                    continue

        except asyncio.CancelledError:
            pass
        except Exception as e:
            for future in self.pending.values():
                if not future.done():
                    future.set_exception(HomeAssistantError(f"Reader failed: {e}"))
            self.pending.clear()

    async def send_command(self, payload: dict, timeout: int = 10):
        current_id = self.msg_id
        self.msg_id += 1

        payload["id"] = current_id
        future = asyncio.get_running_loop().create_future()
        self.pending[current_id] = future

        await self.websocket.send(json.dumps(payload))
        return await asyncio.wait_for(future, timeout=timeout)

    async def get_states(self):
        return await self.send_command({"type": "get_states"})

    async def get_state(self, entity_id: str):
        response = await self.get_states()

        if not response.get("success"):
            raise HomeAssistantError(f"get_states failed: {response}")

        for item in response.get("result", []):
            if item.get("entity_id") == entity_id:
                return item

        return None

    async def turn_on(self, entity_id: str):
        return await self.send_command({
            "type": "call_service",
            "domain": "switch",
            "service": "turn_on",
            "service_data": {"entity_id": entity_id},
        })

    async def turn_off(self, entity_id: str):
        return await self.send_command({
            "type": "call_service",
            "domain": "switch",
            "service": "turn_off",
            "service_data": {"entity_id": entity_id},
        })

    async def close(self):
        if self.reader_task:
            self.reader_task.cancel()
        if self.websocket:
            await self.websocket.close()


def get_ha_client() -> HAWebSocketClient:
    if not settings.HA_WS_URL:
        raise HomeAssistantError("HA_WS_URL is not configured")
    if not settings.HA_TOKEN:
        raise HomeAssistantError("HA_TOKEN is not configured")

    return HAWebSocketClient(
        ws_url=settings.HA_WS_URL,
        token=settings.HA_TOKEN,
    )