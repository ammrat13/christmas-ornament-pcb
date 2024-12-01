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
    alpha = config.get(config.CFG_LIGHT_MOVING_AVG)
    lux_moving_avg = alpha * lux_moving_avg + (1 - alpha) * light

    # Check if the light is below the threshold.
    if light < config.get(config.CFG_LIGHT_THRESHOLD):
        platform.LED.value = True
    else:
        platform.LED.value = False

@task.util.periodic(5.0)
async def update():
    val = lux_moving_avg
    val_int = int(val * 1000.0)
    logger.info(f"led: {val:.2f} lx")
    await ble.CHAR_LIGHT_SENSOR_VALUE.write_async(val_int)

async def reconfigure():
    # First, update the RD characteristic with the current configuration.
    cur_config = int(config.get(config.CFG_LIGHT_THRESHOLD) * 10)
    await ble.CHAR_CFG_LIGHT_THRESHOLD_RD.write_async(cur_config)

    # Now, go into the main loop of waiting for changes.
    @task.util.periodic(30.0)
    async def loop():
        # Read the current configuration. If it's the special value of 0xffff,
        # then we don't have any data.
        ble_config = await ble.CHAR_CFG_LIGHT_THRESHOLD_WR.read_async()
        if ble_config == 0xffff:
            return

        # Update the configuration if it's changed. Make sure to update the
        # host's value as well.
        ble_value = ble_config / 10.0
        if ble_value != config.get(config.CFG_LIGHT_THRESHOLD):
            config.set(config.CFG_LIGHT_THRESHOLD, ble_value)
            await ble.CHAR_CFG_LIGHT_THRESHOLD_RD.write_async(ble_config)
            log.info(f"led: threshold set to {ble_value} lx")

    await loop()
