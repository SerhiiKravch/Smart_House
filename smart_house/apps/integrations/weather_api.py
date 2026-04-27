import asyncio

import aiohttp
from django.conf import settings

from .exceptions import WeatherAPIError

REQUEST_TIMEOUT_SECONDS = 10
MAX_RETRIES = 3
BACKOFF_SECONDS = 1


WEATHER_CODES = {
    0: "Ясно",
    1: "Переважно ясно",
    2: "Частково хмарно",
    3: "Похмуро",
    45: "Туман",
    48: "Туман з памороззю",
    51: "Слабка мряка",
    53: "Помірна мряка",
    55: "Сильна мряка",
    61: "Слабкий дощ",
    63: "Помірний дощ",
    65: "Сильний дощ",
    71: "Слабкий сніг",
    73: "Помірний сніг",
    75: "Сильний сніг",
    80: "Слабкі зливи",
    81: "Помірні зливи",
    82: "Сильні зливи",
    95: "Гроза",
    96: "Гроза зі слабким градом",
    99: "Гроза з сильним градом",
}


def get_weather_description(code: int) -> str:
    return WEATHER_CODES.get(code, f"Невідомий код погоди: {code}")


async def get_current_weather():
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": settings.WEATHER_LAT,
        "longitude": settings.WEATHER_LON,
        "current": "temperature_2m,weather_code,cloud_cover,wind_speed_10m",
        "timezone": settings.WEATHER_TIMEZONE,
    }

    last_error = None
    async with aiohttp.ClientSession() as session:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS)
                async with session.get(url, params=params, timeout=timeout) as response:
                    response.raise_for_status()
                    return await response.json()
            except Exception as exc:
                last_error = exc
                is_retryable = isinstance(exc, (aiohttp.ClientError, asyncio.TimeoutError))
                if not is_retryable or attempt == MAX_RETRIES:
                    break
                await asyncio.sleep(BACKOFF_SECONDS * attempt)

    raise WeatherAPIError(
        f"Failed to fetch weather data after {MAX_RETRIES} attempts: {last_error}"
    )
