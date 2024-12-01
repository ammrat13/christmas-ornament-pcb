# EE 256 Final Project: Christmas Ornament

Board files and firmware for my final project for EE 256. I made a relatively
simple project - just a smart christmas ornament.

  * Low-light conditions turn on the LEDs
  * Shaking the ornament flashes the NeoPixels
  * Thresholds and flash parameters configurable via micro-SD card
  * Sensor values, activation statistics, and device health visible over
    Bluetooth LE
  * Supports LiIon batteries
  * Watchdog timer for reliability

## Block Diagram

![Block Diagram](docs/img/block-diagram.png)

## Project Structure
  * `firmware`: code for the MCU
  * `host`: code to communicate with the MCU over Bluetooth LE
  * `kicad`: board files
  * `kicad-lib`: global library files referenced by the board files
