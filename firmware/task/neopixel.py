"""
Task to flash the NeoPixels for some time when acceleration is detected.
"""

import adafruit_adxl34x
import adafruit_logging
import asyncio
import micropython
import supervisor

import ble
import config
import platform
import task.util

logger = adafruit_logging.getLogger()

activation_count = 0
"""The number of times acceleration has been detected, modulo 2**24"""
activation_mask = micropython.const(0xffffff)
"""The mask to apply to `activation_count` to keep it within 24 bits"""

last_activation_ticks = None
"""The time in ticks when the last acceleration was detected"""
last_activation_ticks_changed = asyncio.Event()
"""Event to signal that `last_activation_ticks` has changed"""

_TICKS_PERIOD = micropython.const(1<<29)
_TICKS_MAX = micropython.const(_TICKS_PERIOD-1)

async def accel_run():
    accel_init()
    await accel_loop()

def accel_init():
    # Convert the configuration value to the nearest multiple of 62.5 mg.
    thresh = config.get(config.CFG_ACCELERATION_THRESHOLD)
    thresh = round(thresh / 0.0625)

    platform.ACCELEROMETER.range = adafruit_adxl34x.Range.RANGE_16_G
    platform.ACCELEROMETER.enable_motion_detection(threshold=thresh)

@task.util.periodic(0.2)
async def accel_loop():
    global last_activation_ticks, activation_count

    is_act = platform.ACCELEROMETER.events["motion"]
    if is_act:
        activation_count = (activation_count + 1) & activation_mask
        last_activation_ticks = supervisor.ticks_ms()
        last_activation_ticks_changed.set()

async def np_run():
    np_init()
    await np_loop()

def np_init():
    platform.NEOPIXEL.fill((0, 0, 0))
    platform.NEOPIXEL.show()

async def np_loop():
    while True:

        # If we have no last activation, wait for one to happen.
        if last_activation_ticks is None:
            await last_activation_ticks_changed.wait()
            last_activation_ticks_changed.clear()
            continue
        # If too much time has passed since the last activation, we'll wait for
        # an acceleration event to happen.
        current_ticks = supervisor.ticks_ms()
        delta_ticks = (current_ticks - last_activation_ticks) & _TICKS_MAX
        max_delta_s = config.get(config.CFG_NEOPIXEL_FLASH_TIME)
        if delta_ticks > 1000.0 * max_delta_s:
            await last_activation_ticks_changed.wait()
            last_activation_ticks_changed.clear()
            continue

        # Flash the NeoPixels for one round.
        for i in range(platform.NEOPIXEL_LEN + 1):
            platform.NEOPIXEL.fill((0, 0, 0))
            if i < platform.NEOPIXEL_LEN:
                br = config.get(config.CFG_NEOPIXEL_BRIGHTNESS)
                platform.NEOPIXEL[i] = (br, br, br)
            platform.NEOPIXEL.show()
            await asyncio.sleep(config.get(config.CFG_NEOPIXEL_FLASH_SPEED))

@task.util.periodic(5.0)
async def update():
    logger.info(f"neopixel: activated {activation_count} times")
    await ble.CHAR_ACCELEROMETER_COUNT.write_async(activation_count)

async def reconfigure():
    # First, update the RD characteristic with the current configuration.
    cur_config = int(config.get(config.CFG_ACCELERATION_THRESHOLD) * 1000)
    await ble.CHAR_CFG_ACCELERATION_THRESHOLD_RD.write_async(cur_config)

    # Now, go into the main loop of waiting for changes.
    @task.util.periodic(30.0)
    async def loop():
        # Read the current configuration. If it's the special value of, then we
        # don't have any data.
        ble_config = await ble.CHAR_CFG_ACCELERATION_THRESHOLD_WR.read_async()
        logger.debug(f"neopixel: read configuration {ble_config:04x}")
        if ble_config == 0xffff:
            return

        # Update the configuration if it's changed.
        ble_value = ble_config / 1000
        if ble_value != config.get(config.CFG_ACCELERATION_THRESHOLD):
            # Set the threshold on the accelerometer.
            thresh = round(ble_value / 0.0625)
            platform.ACCELEROMETER.enable_motion_detection(threshold=thresh)
            # Set the configuration and update the host's value as well.
            config.set(config.CFG_ACCELERATION_THRESHOLD, ble_value)
            await ble.CHAR_CFG_ACCELERATION_THRESHOLD_RD.write_async(ble_config)
            logger.info(f"neopixel: threshold set to {ble_value} g")

    await loop()
