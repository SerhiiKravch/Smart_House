import asyncio
from django.core.management.base import BaseCommand
from django.conf import settings

from apps.integrations.home_assistant import get_ha_client
from apps.automation.services import control_socket


class Command(BaseCommand):
    help = "Run automation loop"

    async def runner(self):
        client = get_ha_client()
        await client.connect()

        try:
            while True:
                wait_seconds = await control_socket(client, settings.HA_ENTITY_ID)
                await asyncio.sleep(wait_seconds)
        finally:
            await client.close()

    def handle(self, *args, **options):
        asyncio.run(self.runner())