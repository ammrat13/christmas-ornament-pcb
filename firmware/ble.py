"""
Module for managing the Bluefruit LE SPI Friend module.

This module provides a way to set up the GATT service on the module, and a way
to update the characteristics of the service. It also provides a way to read
the characteristics.
"""

import adafruit_logging
import platform

logger = adafruit_logging.getLogger()

DEVICE_NAME = b"Ammar Ratnani EE 256"
SERVICE_UUID = b"89-52-25-FE-AC-AF-4F-21-B0-E7-1A-DB-51-E1-16-53"

class BLECharacteristic:
    """
    Each characteristic has the index into the table, as well as a UUID. It also
    has a way to parse values from the module and serialize values for it.
    """

    def __init__(self, index, uuid_bytes, initial_value):
        self.index = index
        self.index_bytes = str(index).encode("utf-8")
        self.uuid_bytes = uuid_bytes
        self.initial_value = initial_value
        self.initial_value_bytes = self._serialize(initial_value).encode("utf-8")

    def read(self):
        res = (platform.BLE.command_check_OK(b"AT+GATTCHAR=" + self.index_bytes)
                .decode("utf-8")
                .strip())
        return self._deserialize(res)

    def write(self, value):
        ser = self._serialize(value).encode("utf-8")
        platform.BLE.command_check_OK(b"AT+GATTCHAR=" + self.index_bytes + b"," + ser)

    def add(self):
        """
        Add the characteristic to the service. Different characteristics might
        want to do this in different ways, so this has to be implemented.
        """
        raise NotImplementedError()

    def _serialize(self, value):
        """
        Take the value and return something that can be passed to `AT+GATTCHAR`.
        It should be a `str`, not a `bytes`.
        """
        raise NotImplementedError()

    def _deserialize(self, serialized):
        """
        Take the output of `AT+GATTCHAR` and return the value. It should be a
        `str`, not a `bytes`.
        """
        raise NotImplementedError()

    def _check_index(self, response):
        """
        Check that the response for adding a characteristic returned the index
        we expected.
        """
        return int(response.decode("utf-8").strip()) == self.index

BLE_CHARACTERISTIC_PROPERTIES_READONLY = b"0x02"
"""Properties for a characteristic that the host can only read."""

class UIntBLECharacteristic(BLECharacteristic):
    """
    A characteristic that represents an unsigned integer. It can have arbitrary
    length, and can be read-only or read-write.
    """

    def __init__(
        self,
        index,
        uuid_bytes,
        properties_bytes=BLE_CHARACTERISTIC_PROPERTIES_READONLY,
        length=4,
        initial_value=0
    ):
        super().__init__(index, uuid_bytes, initial_value)
        self.properties_bytes = properties_bytes
        self.length_bytes = str(length).encode("utf-8")

    def _serialize(self, value):
        return hex(value)

    def _deserialize(self, serialized):
        return int(serialized.replace("-", ""), 16)

    def add(self):
        res = platform.BLE.command_check_OK(
            b"AT+GATTADDCHAR=UUID="
            + self.uuid_bytes
            + b",PROPERTIES="
            + self.properties_bytes
            + b",MIN_LEN="
            + self.length_bytes
            + b",MAX_LEN="
            + self.length_bytes
            + b",VALUE="
            + self.initial_value_bytes)
        if not self._check_index(res):
            raise RuntimeError("Wrong index for characteristic.")

# BLE Characteristics
#
# These are the characteristics that we want to expose to the host. They must
# all be registered in the `_characteristics` list below. The IDs must also be
# what the module returns.

CHAR_HEAP_FREE = UIntBLECharacteristic(1, b"0x0002", length=4, initial_value=0xffffffff)
"""The amount of free heap space on the device, in bytes."""
CHAR_BATTERY_ADC = UIntBLECharacteristic(2, b"0x0003", length=2, initial_value=0)
"""The battery voltage as a raw ADC value."""

_characteristics = [
    CHAR_HEAP_FREE,
    CHAR_BATTERY_ADC,
]
"""List of all the characteristics."""

def dump_info():
    """
    Dump the result of `ATI` and `AT+GATTLIST` to the log.
    """

    ati_res = platform.BLE.command_check_OK(b"ATI")
    ati_res = ati_res.decode("utf-8").strip()
    logger.info("Result of ATI:")
    for line in ati_res.split("\n"):
        logger.info(f"    {line}")

    gatt_res = platform.BLE.command_check_OK(b"AT+GATTLIST")
    if gatt_res is None:
        logger.info("No GATT services.")
        return

    gatt_res = gatt_res.decode("utf-8").strip()
    logger.info("Result of AT+GATTLIST:")
    for line in gatt_res.split("\n"):
        logger.info(f"    {line}")


def factory_reset():
    """
    Reset the module to its "default" state.

    This will repopulate the module with the services and characteristics that
    we define here.
    """

    logger.debug("Resetting the BLE module...")

    # Completely reset the device
    platform.BLE.command_check_OK(b"AT+FACTORYRESET", delay=1.0)
    logger.debug("    factory reset device.")

    # Set the device name
    platform.BLE.command_check_OK(b"AT+GAPDEVNAME=" + DEVICE_NAME)
    platform.BLE.command_check_OK(b"ATZ", delay=1.0)
    logger.debug("    set device name.")

    # Create the service
    platform.BLE.command_check_OK(b"AT+GATTADDSERVICE=UUID128=" + SERVICE_UUID)
    logger.debug("    added service.")

    # Add the characteristics
    for char in _characteristics:
        char.add()
        logger.debug(f"    added characteristic {char.index}.")
    platform.BLE.command_check_OK(b"ATZ", delay=1.0)

def set_initial_values():
    """
    Set all the characteristics to their initial values.
    """
    logger.debug("Setting all characteristics to initial values...")
    for char in _characteristics:
        char.write(char.initial_value)
        logger.debug(f"    set characteristic {char.index} to {char.initial_value}.")
