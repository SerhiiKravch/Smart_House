import asyncio
import aiohttp
import json


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
    56: "Слабка переохолоджена мряка",
    57: "Сильна переохолоджена мряка",
    61: "Слабкий дощ",
    63: "Помірний дощ",
    65: "Сильний дощ",
    66: "Слабкий переохолоджений дощ",
    67: "Сильний переохолоджений дощ",
    71: "Слабкий сніг",
    73: "Помірний сніг",
    75: "Сильний сніг",
    77: "Снігові зерна",
    80: "Слабкі зливи",
    81: "Помірні зливи",
    82: "Сильні зливи",
    85: "Слабкі снігові заряди",
    86: "Сильні снігові заряди",
    95: "Гроза",
    96: "Гроза зі слабким градом",
    99: "Гроза з сильним градом",
}


def get_weather_description(code: int) -> str:
    return WEATHER_CODES.get(code, f"Невідомий код погоди: {code}")


async def get_current_weather():
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 49.8397,
        "longitude": 24.0297,
        "current": "temperature_2m,weather_code,cloud_cover,wind_speed_10m",
        "timezone": "Europe/Kyiv",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.json()


async def weather_api():
    data = await get_current_weather()
    current = data["current"]

    weather_code = current["weather_code"]
    weather_state = get_weather_description(weather_code)

    print(json.dumps(data, indent=2, ensure_ascii=False))

    print("Погода зараз у Львові:")
    print("Час:", current["time"])
    print("Температура:", current["temperature_2m"], "°C")
    print("Хмарність:", current["cloud_cover"], "%")
    print("Вітер:", current["wind_speed_10m"], "км/год")
    print("Погодний стан:", weather_state)
    print("Код погоди:", weather_code)

asyncio.run(weather_api())