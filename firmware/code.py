# Importing this file will also run the platform initialization code, so this
# has to come first.
import platform

import adafruit_logging

import config

logger = adafruit_logging.getLogger()
logger.setLevel(adafruit_logging.DEBUG)

def initialize_config():
    """
    Initialize the configuration from the SD card.

    This is not `async`. It must be called before the main event loop.
    Additionally, this must be done before initializing the bluetooth module.

    See: https://docs.circuitpython.org/projects/sd/en/latest/
    """

    # Try to open the configuration file. If it doesn't work, it's fine. Just
    # log a warning and use the default configuration.
    try:
        with open("/sd/config.txt") as f:
            for line in f:
                config.parse_config_line(line)
    except OSError:
        logger.warning("Failed to open the configuration file.")

    config.dump_config()

if __name__ == "__main__":

    logger.info("Initialized the platform!")

    logger.info("Initializing the configuration...")
    initialize_config()
