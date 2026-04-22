import aiohttp
from django.conf import settings
from .dto import SolarData

from .exceptions import SolarAPIError


async def request_api(session, url, payload, headers):
    async with session.post(url, json=payload, headers=headers) as response:
        response.raise_for_status()
        return await response.json()


async def get_raw_solar_data():
    url = settings.SOLAR_API_URL
    token = settings.SOLAR_API_TOKEN

    if not url:
        raise SolarAPIError("SOLAR_API_URL is not configured")
    if not token:
        raise SolarAPIError("SOLAR_API_TOKEN is not configured")

    payload = {
        # тут твій payload
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        async with aiohttp.ClientSession() as session:
            data = await request_api(session, url, payload, headers)
            return data
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
    return data.get("batterySOC")