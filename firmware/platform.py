"""
Classes for all the peripherals on the PCB.

Importing this file will also run the platform initialization code, which just
mounts the SD card and resets the bluetooth module. This should be the first
thing imported in `code.py`.
"""

import adafruit_adxl34x
import adafruit_sdcard
import adafruit_veml7700
import analogio
import board
import busio
import digitalio
import neopixel
import storage

import driver.bluefruitspi

# Pins
LED_PIN = board.D13
NEOPIXEL_PIN = board.D12
BATTERY_PIN = board.BATTERY
USD_CS_PIN = board.D6
BLE_CS_PIN = board.D9
BLE_RST_PIN = board.D10
BLE_IRQ_PIN = board.D11

# Busses
SPI_BUS = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
I2C_BUS = busio.I2C(board.SCL, board.SDA)

# LED
LED = digitalio.DigitalInOut(LED_PIN)
LED.direction = digitalio.Direction.OUTPUT
# NeoPixel
NEOPIXEL = neopixel.NeoPixel(NEOPIXEL_PIN, 2, auto_write=False)
# Battery
BATTERY = analogio.AnalogIn(BATTERY_PIN)

# I2C Peripherals
LIGHT_SENSOR = adafruit_veml7700.VEML7700(I2C_BUS)
ACCELEROMETER = adafruit_adxl34x.ADXL343(I2C_BUS, address=0x1d)

# microSD Card. This has to be initialized before the bluetooth module since the
# SPI bus is shared between them. The documentation says not doing so messes
# with the initialization of the microSD card.
USD_CS = digitalio.DigitalInOut(USD_CS_PIN)
USD = adafruit_sdcard.SDCard(SPI_BUS, USD_CS)
USD_VFS = storage.VfsFat(USD)
storage.mount(USD_VFS, "/sd")

# Bluetooth Module
BLE_CS = digitalio.DigitalInOut(BLE_CS_PIN)
BLE_RST = digitalio.DigitalInOut(BLE_RST_PIN)
BLE_IRQ = digitalio.DigitalInOut(BLE_IRQ_PIN)
BLE = driver.bluefruitspi.BluefruitSPI(SPI_BUS, BLE_CS, BLE_IRQ, BLE_RST)
BLE.init()
BLE.command_check_OK(b"ATZ")
