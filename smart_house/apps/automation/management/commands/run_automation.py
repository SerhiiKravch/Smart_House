import asyncio
import logging
from django.core.management.base import BaseCommand

from apps.integrations.exceptions import HomeAssistantError
from apps.integrations.home_assistant import get_ha_client
from apps.automation.services import run_automation_cycle

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run automation loop"

    reconnect_sleep_seconds = 10

    async def runner(self):
        while True:
            client = get_ha_client()
            try:
                logger.info("Connecting to Home Assistant...")
                await client.connect()
                logger.info("Connected to Home Assistant")

                while True:
                    try:
                        wait_seconds = await run_automation_cycle(client)
                    except Exception:
                        logger.exception("Automation cycle failed")
                        wait_seconds = 10
                    await asyncio.sleep(wait_seconds)
            except HomeAssistantError:
                logger.exception(
                    "Home Assistant connection error. Retrying in %ss",
                    self.reconnect_sleep_seconds,
                )
            except Exception:
                logger.exception(
                    "Unexpected automation error. Retrying in %ss",
                    self.reconnect_sleep_seconds,
                )
            finally:
                try:
                    await client.close()
                finally:
                    logger.info("Home Assistant connection closed")

            await asyncio.sleep(self.reconnect_sleep_seconds)

    def handle(self, *args, **options):
        logger.info("Starting run_automation command")
        asyncio.run(self.runner())
