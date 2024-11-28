"""
A task for monitoring the heap usage of the CircuitPython VM.
"""

import adafruit_logging
import gc

import ble
import task.util

logger = adafruit_logging.getLogger()

@task.util.periodic(10)
async def run():
    free = gc.mem_free()
    logger.debug(f"heap_monitor: {free} bytes free")
    ble.CHAR_HEAP_FREE.write(free)
