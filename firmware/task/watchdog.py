"""Task to periodically pet the watchdog to prevent a reset."""

from microcontroller import watchdog as WATCHDOG

async def run():
    while True:
        WATCHDOG.feed()
        await asyncio.sleep(config.get(config.CFG_WATCHDOG_PET_INTERVAL))
