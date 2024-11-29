"""
Task to turn on the lights when the light sensor detects low light.
"""

import adafruit_logging
import asyncio

import ble
import config
import platform
import task.util

logger = adafruit_logging.getLogger()

lux_moving_avg = 0.0
"""Average light level."""

@task.util.periodic(0.2)
async def run():

    # Read the light sensor.
    light = platform.LIGHT_SENSOR.lux

    # Update the moving average.
    global lux_moving_avg
    alpha = config.get(config.CFG_LIGHT_MOVING_AVG.ident)
    lux_moving_avg = alpha * lux_moving_avg + (1 - alpha) * light

    # Check if the light is below the threshold.
    if light < config.get(config.CFG_LOW_LIGHT_THRESHOLD.ident):
        platform.LED.value = True
    else:
        platform.LED.value = False

@task.util.periodic(5.0)
async def update():
    val = lux_moving_avg
    val_int = int(val * 1000.0)
    logger.info(f"light_sensing: {val:.2f} lx")
    await ble.CHAR_LIGHT_SENSOR.write_async(val_int)
