import asyncio

import aiohttp
from django.conf import settings
from .dto import SolarData

from .exceptions import SolarAPIError

REQUEST_TIMEOUT_SECONDS = 10
MAX_RETRIES = 3
BACKOFF_SECONDS = 1


def _is_retryable(exc: Exception) -> bool:
    return isinstance(exc, (aiohttp.ClientError, asyncio.TimeoutError))


async def request_api(session, url, payload, headers):
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS)
            async with session.post(
                url,
                json=payload,
                headers=headers,
                timeout=timeout,
            ) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as exc:
            last_error = exc
            if not _is_retryable(exc) or attempt == MAX_RETRIES:
                break
            await asyncio.sleep(BACKOFF_SECONDS * attempt)

    raise SolarAPIError(f"Solar API request failed after {MAX_RETRIES} attempts: {last_error}")


async def get_raw_solar_data():
    BASE_URL = settings.SOLAR_API_URL
    token = settings.SOLAR_API_TOKEN
    station = settings.STATION_ID

    if not BASE_URL:
        raise SolarAPIError("SOLAR_API_URL is not configured")
    if not token:
        raise SolarAPIError("SOLAR_API_TOKEN is not configured")

    url = f"{BASE_URL}/v1.0/station/latest"

    payload = {
        "stationId": station
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        async with aiohttp.ClientSession() as session:
            data = await request_api(session, url, payload, headers)
            return data
    except SolarAPIError:
        raise
    except Exception as e:
        raise SolarAPIError(f"Failed to fetch solar data: {e}") from e


async def get_selected_data():
    data = await get_raw_solar_data()

    return SolarData(
        generation_power=data.get("generationPower"),
        wire_power=data.get("wirePower"),
        consumption_power=data.get("consumptionPower"),
        battery_soc=data.get("batterySOC"),
    )


async def get_battery_soc():
    data = await get_selected_data()
    return data.battery_soc
