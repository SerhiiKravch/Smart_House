import aiohttp
from django.conf import settings

from .exceptions import WeatherAPIError


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

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.json()
    except Exception as e:
        raise WeatherAPIError(f"Failed to fetch weather data: {e}") from e