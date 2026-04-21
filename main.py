import asyncio
import json
from datetime import datetime
from zoneinfo import ZoneInfo

import websockets
import solar_api, weather_api

import os
from dotenv import load_dotenv

load_dotenv()


CLEAR_WEATHER_CODES = {0, 1, 2, 3}   
CHECK_INTERVAL = 600           




class HAWebSocketClient:
    def __init__(self, ws_url, token):
        self.ws_url = ws_url
        self.token = token
        self.websocket = None
        self.msg_id = 1
        self.pending = {}
        self.reader_task = None

    async def connect(self):
        self.websocket = await websockets.connect(self.ws_url)

        msg = json.loads(await self.websocket.recv())
        print("Server: ", msg)

        await self.websocket.send(json.dumps({
            "type": "auth",
            "access_token": self.token
        }))

        msg = json.loads(await self.websocket.recv())
        print("Auth response: ", msg)

        if msg.get("type") != "auth_ok":
            raise Exception("Auth error occurs")
        
        self.reader_task = asyncio.create_task(self._reader())

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

                if data.get("type") == "event":
                    event = data.get("event", {})
                    event_data = event.get("data", {})
                    entity_id = event_data.get("entity_id")
                    new_state = event_data.get("new_state")
                    old_state = event_data.get("old_state")

                    print("\n[EVENT]")
                    print("entity_id:", entity_id)
                    print("було:", old_state.get("state") if old_state else None)
                    print("стало:", new_state.get("state") if new_state else None)

                else:
                    print("\n[OTHER MESSAGE]")
                    print(data)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            print("Reader error:", repr(e))

    async def send_command(self, payload):
        current_id = self.msg_id
        self.msg_id += 1

        payload["id"] = current_id

        future = asyncio.get_running_loop().create_future()
        self.pending[current_id] = future

        await self.websocket.send(json.dumps(payload))
        return await asyncio.wait_for(future, timeout=10)
    
    async def subscribe_state_changed(self):
        response = await self.send_command({
            "type": "subscribe_events",
            "event_type": "state_changed"
        })
        return response
    
    async def turn_on(self, entity_id):
        response = await self.send_command({
            "type": "call_service",
            "domain": "switch",
            "service": "turn_on",
            "service_data": {
                "entity_id": entity_id
            }
        })
        return response
    
    async def turn_off(self, entity_id):
        response = await self.send_command({
            "type": "call_service",
            "domain": "switch",
            "service": "turn_off",
            "service_data": {
                "entity_id": entity_id
            }
        })
        return response

    async def toggle(self, entity_id):
        response = await self.send_command({
            "type": "call_service",
            "domain": "switch",
            "service": "toggle",
            "service_data": {
                "entity_id": entity_id
            }
        })
        return response

    async def get_states(self):
        response = await self.send_command({
            "type": "get_states"
        })
        return response

    async def get_state(self, entity_id):
        response = await self.get_states()

        if not response.get("success"):
            return None

        all_states = response.get("result", [])
        for item in all_states:
            if item.get("entity_id") == entity_id:
                return item
        return None

    async def close(self):
        if self.reader_task:
            self.reader_task.cancel()
        if self.websocket:
            await self.websocket.close()


async def control_socket(client, entity_id):

    DAY_CHECK_INTERVAL = 600
    NIGHT_CHECK_INTERVAL = 600


    kyiv_now = datetime.now(ZoneInfo("Europe/Kyiv"))

    is_night_tariff_time_ok = kyiv_now.hour >= 23 or kyiv_now.hour <= 7

    battery_data = await solar_api.get_selected_data()
    if not battery_data:
        print("Не вдалося отримати battery_data")
        return


    is_battery_ok = battery_data.get("batterySOC") is not None and battery_data.get("batterySOC") > 50
    is_energy_outer_ok = battery_data.get("wirePower") is not None and battery_data.get("wirePower") > 0
    is_energy_generated_ok = battery_data.get("generationPower") is not None and battery_data.get("generationPower") > 300

    weather_data = await weather_api.get_current_weather()

    weather_code = None
    weather_text = "Невідомо"
    is_weather_ok = False

    if weather_data and "current" in weather_data:
        weather_code = weather_data["current"].get("weather_code")
        if weather_code is not None:
            weather_text = weather_api.get_weather_description(weather_code)
            is_weather_ok = weather_code in CLEAR_WEATHER_CODES

    night_should_turn_on = is_night_tariff_time_ok and is_battery_ok and is_energy_outer_ok
    day_should_turn_on = is_energy_generated_ok 



    if is_night_tariff_time_ok:
        should_turn_on = night_should_turn_on
        next_check_interval = NIGHT_CHECK_INTERVAL
        mode = "ніч"
    else:
        should_turn_on = day_should_turn_on
        next_check_interval = DAY_CHECK_INTERVAL
        mode = "день"


    print(await client.get_states())

    current_state_data = await client.get_state(entity_id)
    if current_state_data is None:
        print(f"Entity {entity_id} не знайдено в Home Assistant")
        return next_check_interval
    current_state = current_state_data.get("state")



    print("\n--- Перевірка умов ---")
    print("Час:", kyiv_now.strftime("%Y-%m-%d %H:%M:%S"))
    print("Режим:", mode)
    print("Battery Data:", battery_data)
    print("Battery OK:", is_battery_ok)
    print("Outer energy OK:", is_energy_outer_ok)
    print("Generated energy OK:", is_energy_generated_ok)
    print("Weather code:", weather_code)
    print("Weather state:", weather_text)
    print("Weather OK:", is_weather_ok)
    print("Поточний стан розетки:", current_state)
    print("Потрібно увімкнути:", should_turn_on)

    if should_turn_on:
        if current_state != "on":
            print(f"-> Вмикаю розетку ({mode})")
            resp = await client.turn_on(entity_id)
            print("turn_on response:", resp)
        else:
            print(f"-> Розетка вже увімкнена ({mode})")
    else:
        if current_state != "off":
            print(f"-> Вимикаю розетку ({mode})")
            resp = await client.turn_off(entity_id)
            print("turn_off response:", resp)
        else:
            print(f"-> Розетка вже вимкнена ({mode})")

    return next_check_interval


async def main():

    HA_WS_URL = os.getenv("HA_WS_URL")
    TOKEN = os.getenv("HA_TOKEN")
    ENTITY_ID = os.getenv("ENTITY_ID")


    if not HA_WS_URL:
        raise ValueError("Не знайдено HA_WS_URL у .env")
    if not TOKEN:
        raise ValueError("Не знайдено HA_TOKEN у .env")
    if not ENTITY_ID:
        raise ValueError("Не знайдено ENTITY_ID у .env")

    
    client = HAWebSocketClient(HA_WS_URL, TOKEN)
    await client.connect()

    
    try:
        while True:
            try:
                wait_seconds = await control_socket(client, ENTITY_ID)
            except Exception as e:
                print("Помилка в control_socket:", repr(e))
                wait_seconds = 600

            print(f"Наступна перевірка через {wait_seconds // 60} хв")
            await asyncio.sleep(wait_seconds)

    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())