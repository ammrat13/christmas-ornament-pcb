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
