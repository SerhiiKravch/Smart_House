import json
import aiohttp
import asyncio
from datetime import datetime, timedelta

import os
from dotenv import load_dotenv

load_dotenv()


# Налаштування
BASE_URL = "https://eu1-developer.deyecloud.com"
TOKEN = os.getenv("SA_TOKEN")
DEVICE_SN = os.getenv("DEVICE_SN")
STATION_ID = os.getenv("STATION_ID", "61989060")

FILE_NAME = "api_data.jsonl"
INTERVAL_SECONDS = 600  
START_HOUR = 7
END_HOUR = 19  

URL = f"{BASE_URL}/v1.0/station/latest"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}
PAYLOAD = {
    "stationId": STATION_ID
}

SELECTED_KEYS = [
    "generationPower",
    "wirePower",
    "consumptionPower",
    "batterySOC"
]



def is_work_time(now: datetime) -> bool:
    return START_HOUR <= now.hour < END_HOUR


async def sleep_until_next_start():
    now = datetime.now()
    next_start = now.replace(hour=START_HOUR, minute=0, second=0, microsecond=0)

    if now.hour >= END_HOUR:
        next_start += timedelta(days=1)

    sleep_seconds = (next_start - now).total_seconds()

    if sleep_seconds > 0:
        print(
            f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] "
            f"Поза робочим часом. Сон до {next_start.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await asyncio.sleep(sleep_seconds)


def save_jsonl(record, file_name):
    with open(file_name, "a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


async def request_api(session: aiohttp.ClientSession):
    async with session.post(URL, json=PAYLOAD, headers=HEADERS) as response:
        response.raise_for_status()
        data = await response.json(content_type=None)
        return response.status, data


def extract_selected_data(api_response: dict) -> dict:
    # Якщо API повертає {"data": {...}}, беремо вкладений data
    source = api_response.get("data", api_response)

    if not isinstance(source, dict):
        return {}

    return {key: source.get(key) for key in SELECTED_KEYS}


async def main():
    if not TOKEN:
        raise ValueError("Не знайдено SA_TOKEN у .env")

    print("Програма запущена")

    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        while True:
            now = datetime.now()

            if not is_work_time(now):
                await sleep_until_next_start()
                continue

            record = {
                "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
                "url": URL,
                "stationId": STATION_ID
            }

            try:
                status_code, api_response = await request_api(session)
                selected_data = extract_selected_data(api_response)

                record["status_code"] = status_code
                record["data"] = selected_data

                save_jsonl(record, FILE_NAME)

                print(f"[{record['timestamp']}] Дані збережено: {selected_data}")

            except aiohttp.ClientResponseError as e:
                record["status_code"] = e.status
                record["error"] = f"HTTP помилка: {e.status} {e.message}"
                save_jsonl(record, FILE_NAME)

                print(f"[{record['timestamp']}] HTTP помилка: {e.status} {e.message}")

            except aiohttp.ClientError as e:
                record["error"] = f"Помилка запиту: {str(e)}"
                save_jsonl(record, FILE_NAME)

                print(f"[{record['timestamp']}] Помилка запиту: {e}")

            except json.JSONDecodeError as e:
                record["error"] = f"Помилка JSON: {str(e)}"
                save_jsonl(record, FILE_NAME)

                print(f"[{record['timestamp']}] Помилка JSON: {e}")

            except Exception as e:
                record["error"] = f"Інша помилка: {str(e)}"
                save_jsonl(record, FILE_NAME)

                print(f"[{record['timestamp']}] Інша помилка: {e}")

            await asyncio.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())