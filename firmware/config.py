"""
Dictionary for managing configuration variables.

Each configuration option has an integer ID, a human-readable name, and default
value, and a method to parse it from a string. Each configuration option is a
global constant. This file also maintains a `dict` mapping the IDs to their
current values, and provides a method to get and set by ID.
"""

import adafruit_logging
import asyncio

logger = adafruit_logging.getLogger()

class ConfigOption():
    """Abstract class for configuration options."""

    def __init__(self, ident, name, default):
        self.ident = ident
        self.name = name
        self.default = default

    def parse(self, value):
        raise NotImplementedError()

class IntConfigOption(ConfigOption):
    def __init__(self, ident, name, default):
        super().__init__(ident, name, default)
    def parse(self, value):
        return int(value)

class FloatConfigOption(ConfigOption):
    def __init__(self, ident, name, default):
        super().__init__(ident, name, default)
    def parse(self, value):
        return float(value)

class BoolConfigOption(ConfigOption):
    def __init__(self, ident, name, default):
        super().__init__(ident, name, default)
    def parse(self, value):
        return value.lower() == "true"

# Configuration Options
#
# These must all be registered in the `_config_option_registry` list below. The
# IDs must also be unique.

CFG_LIGHT_THRESHOLD = FloatConfigOption(1, "LIGHT_THRESHOLD", 30.0)
"""The light level below which the LEDs will be turned on, in lux."""
CFG_LIGHT_MOVING_AVG = FloatConfigOption(2, "LIGHT_MOVING_AVG", 0.8)
"""The exponential moving average factor for the light sensor."""

CFG_ACCELERATION_THRESHOLD = FloatConfigOption(3, "ACCELERATION_THRESHOLD", 6.25)
"""
The acceleration threshold for detecting acceleration, in g.

Note that the API is in multiples of 62.5 mg. The configuration value will be
rounded to the nearest multiple.
"""

CFG_NEOPIXEL_BRIGHTNESS = IntConfigOption(4, "NEOPIXEL_BRIGHTNESS", 5)
"""The brightness of the NeoPixels when they are flashing, from 0 to 255."""
CFG_NEOPIXEL_FLASH_TIME = FloatConfigOption(5, "NEOPIXEL_FLASH_TIME", 1.0)
"""The time in seconds for the NeoPixels to flash."""
CFG_NEOPIXEL_FLASH_SPEED = FloatConfigOption(6, "NEOPIXEL_FLASH_SPEED", 0.1)
"""The number of seconds to wait between frames of flashing."""

CFG_WATCHDOG_TIMEOUT = FloatConfigOption(7, "WATCHDOG_TIMEOUT", 10.0)
"""The time in seconds before the watchdog will reset the device."""
CFG_WATCHDOG_PET_INTERVAL = FloatConfigOption(8, "WATCHDOG_PET_INTERVAL", 5.0)
"""
The time in seconds between watchdog pets. The task to perform the pet will
become available after this time, but it may not be run immediately.
"""

_config_option_registry = [
    CFG_LIGHT_THRESHOLD,
    CFG_LIGHT_MOVING_AVG,
    CFG_ACCELERATION_THRESHOLD,
    CFG_NEOPIXEL_BRIGHTNESS,
    CFG_NEOPIXEL_FLASH_TIME,
    CFG_NEOPIXEL_FLASH_SPEED,
    CFG_WATCHDOG_TIMEOUT,
    CFG_WATCHDOG_PET_INTERVAL,
]
"""List of all possible configuration options."""

_config_values = {opt.ident: opt.default for opt in _config_option_registry}
"""
Dictionary of current configuration values.

Initially, all the values are set to their default. But, this dictionary can be
updated by the methods below.
"""

def get(opt):
    """
    Get the value of a cofiguration option.
    """
    ident = opt.ident
    assert ident in _config_values
    return _config_values[ident]

def set(opt, value):
    """
    Set the value of a configuration option.
    """
    ident = opt.ident
    assert ident in _config_values
    _config_values[ident] = value

def dump_config():
    """Dump the current configuration to the log."""
    logger.info("Current configuration:")
    for ident, value in _config_values.items():
        logger.info(f"    {ident}: {value}")

def parse_config_line(line):
    """
    Parse a line of the configuration file configuration from a string.

    This method will ignore blank lines and lines starting with a `#`. It will
    just log if the line is not well-formed.
    """
    logger.debug(f"Parsing configuration line: {line}")

    # This ignores all leading and trailing whitespace. In particular, it will
    # work if the line is like `    # comment`.
    line = line.strip()
    if line == "" or line.startswith("#"):
        return
    logger.debug(f"    non-comment non-empty")

    # Each line is expected to be of the form `key = value`.
    parts = line.split("=", 1)
    if len(parts) != 2:
        logger.warning(f"Invalid configuration line: {line}")
        return

    name, value_str = parts
    name = name.strip()
    value_str = value_str.strip()
    logger.debug(f"    name:  {name}")
    logger.debug(f"    value: {value_str}")

    # Find the option with the given name.
    option = None
    for opt in _config_option_registry:
        if opt.name == name:
            option = opt
            break
    if option is None:
        logger.warning(f"Invalid configuration option: {name}")
        return

    # Parse the value.
    try:
        value = option.parse(value_str)
    except Exception:
        logger.warning(f"Invalid configuration value: {value_str}")
        return

    # Set the value. We haven't started using asyncio yet, so we can just access
    # the `_config_values` dictionary directly.
    logger.debug(f"    setting {option.ident} to {value}")
    assert option.ident in _config_values
    _config_values[option.ident] = value
