# Device Firmware

This folder has the CircuitPython firmware for the device. It contains a
`Pipfile` for installing `circup` on the host, as well as a `requirements.txt`
for getting the required libraries onto the device.

To save on space, all the files (except for `code.py`) are compiled. Download
`mpy-cross` and set the `MPY_CROSS` environment variable to that path. If more
files are added, modify `PY_FILES` in the `Makefile` with the new code. Finally,
mount the device at some path `${DEVICE_PATH}` and run
```
$ make all
$ make PREFIX="${DEVICE_PATH}" install
```

## Configuration Files

An example configuration file is given in `config.txt`. It should be placed at
the root of the micro-SD card. Additionally, if a file named `reset-ble` is
present on the root of the micro-SD card, then the Bluefruit LE SPI friend will
be factory-reset and repopulated.

## Register Map

Over Bluetooth LE, this firmware provides a service with some characteristics,
which act as MMIO registers. The registers are defined in `ble.py` as `CHAR_*`.
The service's UUID is given as `SERVICE_UUID`.
