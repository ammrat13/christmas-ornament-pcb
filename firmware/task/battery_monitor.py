"""
A task for monitoring the battery level.
"""

import adafruit_logging

import ble
import platform
import task.util

logger = adafruit_logging.getLogger()

@task.util.periodic(30.0)
async def run():
    adc_val = platform.BATTERY.value
    voltage_val = (adc_val * 2) * 3.3 / 65535.0
    logger.debug(f"battery_monitor: {voltage_val:.2f} V")
    await ble.CHAR_BATTERY_ADC.write_async(adc_val)
