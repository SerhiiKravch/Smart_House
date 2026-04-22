class IntegrationError(Exception):
    pass


class HomeAssistantError(IntegrationError):
    pass


class SolarAPIError(IntegrationError):
    pass


class WeatherAPIError(IntegrationError):
    pass