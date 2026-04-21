import asyncio
import aiohttp
import json
import websockets


import os
from dotenv import load_dotenv

load_dotenv()


BASE_URL = "https://eu1-developer.deyecloud.com"   # pick your datacenter
#BASE_URL = "https://us1-developer.deyecloud.com"   # pick your datacenter
#BASE_URL = "https://india-developer.deyecloud.com"   # pick your datacenter
TOKEN = os.getenv("SA_TOKEN")

DEVICE_SN = os.getenv("DEVICE_SN")

# #url = f"{BASE_URL}/v1.0/device/latest"
# url = f"{BASE_URL}/v1.0/device/list"
# headers = {
#     "Authorization": f"Bearer {TOKEN}",
#     "Content-Type": "application/json",
# }

# payload = {
#     "deviceList" : [DEVICE_SN]
# }
# payload = {"page": 1, "size": 20}



# class DCWebSocketClient:
#     def _init_(self, ws_url, token):
#         self.ws_url = ws_url
#         self.token = token
#         self.websocket = None
#         self.headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
#         self.reader_task = None

#     async def connect(self):
#         self.websocket = await websockets.connect(self.ws_url)

#         msg = json.loads(await self.websocket.recv())
#         print("Server: ", msg)

#         await self.websocket.send(json.dumps(self.headers))

#         msg = json.loads(await self.websocket.recv())
#         print("Auth response: ", msg)

#         if msg.get("type") != "auth_ok":
#             raise Exception("Auth error occurs")
        
#         self.reader_task = asyncio.create_task(self._reader())
    
#     async def _reader(self):
#         try:
#             while True:
#                 raw = await self.websocket.recv()
#                 data = json.loads(raw)
#         except asyncio.CancelledError:
#             pass



#url = f"{BASE_URL}/v1.0/device/list"
url = f"{BASE_URL}/v1.0/station/latest"
headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
payload = {  "stationId": 61989060 }


async def request_api(session, url, payload, headers):
    async with session.post( url, json=payload, headers=headers ) as response:
        response.raise_for_status()
        return await response.json()
        

async def get_selected_data():
    async with aiohttp.ClientSession() as session:
        data = await request_api(session, url, payload, headers)
        
        keys = ['generationPower', 'wirePower', 'consumptionPower', 'batterySOC']

        selected = {key: data.get(key) for key in keys}

        print("\nReceived data:")
        print(selected)

        return selected



async def get_battery_soc():
    async with aiohttp.ClientSession() as session:
        data = await request_api(session, url, payload, headers)
        print("\nReceived data:")
        print(data)

        battery_soc = data.get("batterySOC")
        return battery_soc


async def main_requests():
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                data = await request_api(session, url, payload, headers)
                print("\nRecieved data:")
                print(data)

                battary_soc = data["batterySOC"]

                print("\nBattary SOC:")
                print(battary_soc)

            except Exception as e:
                print("Error: ", e)

            await asyncio.sleep(600)

# asyncio.run(main_requests())