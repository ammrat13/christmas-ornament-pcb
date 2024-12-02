"""
Entrypoint for the CircuitPython application. The `code.py` file just calls the
`main` function from this file.
"""

# Importing this file will also run the platform initialization code, so this
# has to come first.
import platform

from micropython import const

import adafruit_logging
import asyncio
import gc
import microcontroller
import os
import supervisor
import time
import watchdog

import ble
import config
import task

_S_IFREG = const(0o100000)
"""
Used for checking if `reset-ble` is a regular file.
See: https://man7.org/linux/man-pages/man7/inode.7.html
"""

_CTRL_C_TIMEOUT = const(5.0)
"""How long to wait for a Ctrl-C before starting the program."""

logger = adafruit_logging.getLogger()
logger.setLevel(adafruit_logging.DEBUG)

def prompt_repl():
    """
    Prompt the user to enter the REPL. Wait for a response for some time, before
    returning to the main program. This is useful for debugging purposes.
    Returns whether the user entered the REPL.
    """

    logger.info("Press Ctrl-C to enter the REPL.")
    logger.info("Otherwise, the program will start in 5 seconds.")

    try:
        time.sleep(_CTRL_C_TIMEOUT)
        return False
    except KeyboardInterrupt:
        logger.info("Detected Ctrl-C.")
        return True

    logger.info("Starting the program...")

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
        ble.factory_reset(config.get(config.CFG_DEVICE_NAME))
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
    if prompt_repl():
        return

    initialize_config()

    initialize_ble()
    increment_boot_count()

    # The initialization code creates a lot of garbage. Let's clean it up.
    gc.collect()

    # Initialize the watchdog last, since it can kill us if we take too long
    # after this point.
    initialize_watchdog()

    # Start the main task. If we die for any reason, just reset the board. This
    # will also automatically `deinit` the watchdog.
    try:
        asyncio.run(task.run())
    finally:
        logger.error("Main loop died - resetting")
        supervisor.reload()
