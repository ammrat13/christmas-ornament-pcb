"""
Entrypoint for the CircuitPython application. The `code.py` file just calls the
`main` function from this file.
"""

# Importing this file will also run the platform initialization code, so this
# has to come first.
import platform

import adafruit_logging
import asyncio
import gc
import microcontroller
import os
import watchdog

import ble
import config
import task

_S_IFREG = const(0o100000)
"""
Used for checking if `reset-ble` is a regular file.
See: https://man7.org/linux/man-pages/man7/inode.7.html
"""

logger = adafruit_logging.getLogger()
logger.setLevel(adafruit_logging.DEBUG)

def initialize_config():
    """
    Initialize the configuration from the SD card.

    This is not `async`. It must be called before the main event loop.
    Additionally, this must be done before initializing the bluetooth module.

    See: https://docs.circuitpython.org/projects/sd/en/latest/
    """

    logger.info("Initializing the configuration...")

    # Try to open the configuration file. If it doesn't work, it's fine. Just
    # log a warning and use the default configuration.
    try:
        with open("/sd/config.txt") as f:
            for line in f:
                config.parse_config_line(line)
    except OSError:
        logger.warning("Failed to open the configuration file.")

    config.dump_config()

def initialize_ble():
    """
    Initialize the BLE module. We'll factory-reset it if we have to. In any
    case, we'll set all the characteristics to be their initial values. We'll
    also dump to the log.
    """

    # Determine whether `/sd/reset-ble` exists and is a regular file.
    reset_file_found = False
    try:
        stat_res = os.stat("/sd/reset-ble")
        if stat_res[0] != _S_IFREG:
            logger.debug("File `/sd/reset-ble` exists, but is not a regular file")
        else:
            logger.debug("Found `/sd/reset-ble` - will factory reset")
            reset_file_found = True
    except OSError:
        logger.debug("Did not find `/sd/reset-ble`")

    if reset_file_found:
        ble.factory_reset()
        os.remove("/sd/reset-ble")
        os.sync()

    ble.set_initial_values()
    ble.dump_info()

def initialize_watchdog():
    timeout = config.get(config.CFG_WATCHDOG_TIMEOUT)
    logger.debug(f"Initializing the watchdog with timeout {timeout}")
    microcontroller.watchdog.timeout = timeout
    microcontroller.watchdog.mode = watchdog.WatchDogMode.RESET

def increment_boot_count():
    """Increment the boot count reported over BLE."""
    boot_count = ble.CHAR_BOOT_COUNT.read()
    boot_count += 1
    ble.CHAR_BOOT_COUNT.write(boot_count)
    logger.debug(f"Boot count: {boot_count}")

def main():
    logger.info("Got to `main`!")

    initialize_config()

    initialize_ble()
    increment_boot_count()

    # The initialization code creates a lot of garbage. Let's clean it up.
    gc.collect()

    # Initialize the watchdog last, since it can kill us if we take too long
    # after this point.
    initialize_watchdog()

    asyncio.run(task.run())
