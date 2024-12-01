"""Task to periodically pet the watchdog to prevent a reset."""

import asyncio
import microcontroller

import config

async def run():
    while True:
        microcontroller.watchdog.feed()
        await asyncio.sleep(config.get(config.CFG_WATCHDOG_PET_INTERVAL))
