from dataclasses import dataclass
from typing import Optional


@dataclass
class SolarData:
    generation_power: Optional[float]
    wire_power: Optional[float]
    consumption_power: Optional[float]
    battery_soc: Optional[float]


@dataclass
class WeatherData:
    weather_code: Optional[int]
    weather_description: str
    temperature: Optional[float]
    cloud_cover: Optional[float]
    wind_speed: Optional[float]


@dataclass
class SocketState:
    entity_id: str
    state: Optional[str]


@dataclass
class ControlDecision:
    should_turn_on: bool
    reason: str
    mode: str   # "day" або "night"
    next_check_interval: int