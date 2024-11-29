"""
Custom driver for the Adafruit Bluefruit LE SPI Friend.

The driver in the library doesn't exactly fit our needs. In particular, it
doesn't play nicely with `asyncio`. We also take this opportunity to strip out
some of the functionality that we don't need.

See: https://github.com/adafruit/Adafruit_CircuitPython_BluefruitSPI
"""

import time
import struct

from digitalio import Direction, Pull
from adafruit_bus_device.spi_device import SPIDevice
from micropython import const

import asyncio

_MSG_COMMAND = const(0x10)  # Command message
_MSG_RESPONSE = const(0x20)  # Response message
_MSG_ALERT = const(0x40)  # Alert message
_MSG_ERROR = const(0x80)  # Error message

_SDEP_INITIALIZE = const(0xBEEF)  # Resets the Bluefruit device
_SDEP_ATCOMMAND = const(0x0A00)  # AT command wrapper
_SDEP_BLEUART_TX = const(0x0A01)  # BLE UART transmit data
_SDEP_BLEUART_RX = const(0x0A02)  # BLE UART read data


class BluefruitSPI:
    """Helper for the Bluefruit LE SPI Friend"""

    @staticmethod
    def _create_sdep_raw(dest, payload, more):
        """
        Create an SDEP packet

        :param dest: bytearray(20) to place SDEP packet in
        :param payload: iterable with length <= 16 containing the payload data
        :param more: True to set the more bit, False otherwise
        """
        _more = 0x80 if more else 0
        plen = len(payload)
        struct.pack_into(
            "<BHB16s",
            dest,
            0,
            _MSG_COMMAND,
            _SDEP_ATCOMMAND,
            plen | _more,
            payload,
        )

    def __init__(
        self,
        spi,
        cs,  # pylint: disable=invalid-name
        irq,
        reset,
    ):  # pylint: disable=too-many-arguments
        self._irq = irq
        self._buf_tx = bytearray(20)
        self._buf_rx = bytearray(20)

        # Reset
        reset.direction = Direction.OUTPUT
        reset.value = False
        time.sleep(0.01)
        reset.value = True
        time.sleep(0.5)

        # CS is an active low output
        cs.direction = Direction.OUTPUT
        cs.value = True

        # irq line is active high input, so set a pulldown as a precaution
        self._irq.direction = Direction.INPUT
        self._irq.pull = Pull.DOWN

        self._spi_device = SPIDevice(spi, cs, baudrate=4000000, phase=0, polarity=0)

        # This lock must be acquired during the process of sending a command
        # from an `asyncio` context. Additionally, the normal `command` methods
        # should not be used after the `async` methods are used.
        self._cmd_lock = asyncio.Lock()

    def init(self):
        """
        Sends the SDEP initialize command, which causes the board to reset.
        This command should complete in under 1s.
        """
        # Construct the SDEP packet
        struct.pack_into("<BHB", self._buf_tx, 0, _MSG_COMMAND, _SDEP_INITIALIZE, 0)

        # Send out the SPI bus
        with self._spi_device as spi:
            spi.write(self._buf_tx, end=4)  # pylint: disable=no-member

        # Wait 1 second for the command to complete.
        time.sleep(1)

    def _cmd(self, cmd):  # pylint: disable=too-many-branches
        """
        Executes the supplied AT command, which must be terminated with
        a new-line character.
        Returns msgtype, rspid, rsp, which are 8-bit int, 16-bit int and a
        bytearray.

        :param cmd: The new-line terminated AT command to execute.
        """

        # We don't want to interrupt any existing sends
        assert not self._cmd_lock.locked()

        # Make sure we stay within the 255 byte limit
        if len(cmd) > 127:
            raise ValueError("Command too long.")

        more = True
        pos = 0
        while len(cmd) - pos:
            # Construct the SDEP packet
            if len(cmd) - pos <= 16:
                # Last or sole packet
                more = False
            plen = len(cmd) - pos
            plen = min(plen, 16)
            self._create_sdep_raw(self._buf_tx, cmd[pos : pos + plen], more=more)

            # Update the position if there is data remaining
            pos += plen

            # Send out the SPI bus
            time.sleep(0.05)
            with self._spi_device as spi:
                spi.write(self._buf_tx, end=len(cmd) + 4)  # pylint: disable=no-member

        # Wait up to 200ms for a response
        timeout = 0.2
        while timeout > 0 and not self._irq.value:
            time.sleep(0.01)
            timeout -= 0.01
        if timeout <= 0:
            raise RuntimeError("Timed out waiting for a response.")

        # Retrieve the response message
        msgtype = 0
        rspid = 0
        rsplen = 0
        rsp = b""
        while self._irq.value is True:
            # Read the current response packet
            time.sleep(0.01)
            with self._spi_device as spi:
                spi.readinto(self._buf_rx)

            # Read the message envelope and contents
            msgtype, rspid, rsplen = struct.unpack(">BHB", self._buf_rx[0:4])
            if rsplen >= 16:
                rsp += self._buf_rx[4:20]
            else:
                rsp += self._buf_rx[4 : rsplen + 4]

            time.sleep(0.05)

        return msgtype, rspid, rsp

    def command(self, string):
        """Send a command and check response code"""
        try:
            msgtype, msgid, rsp = self._cmd(string + "\n")
            if msgtype == _MSG_ERROR:
                raise RuntimeError("Error (id:{0})".format(hex(msgid)))
            if msgtype == _MSG_RESPONSE:
                return rsp
            raise RuntimeError("Unknown response (id:{0})".format(hex(msgid)))
        except RuntimeError as error:
            raise RuntimeError("AT command failure: " + repr(error)) from error

    def command_check_OK(self, command, delay=0.0):  # pylint: disable=invalid-name
        """Send a fully formed bytestring AT command, and check
        whether we got an 'OK' back. Returns payload bytes if there is any"""
        ret = self.command(command)
        time.sleep(delay)
        if not ret or not ret[-4:]:
            raise RuntimeError("Not OK")
        if ret[-4:] != b"OK\r\n":
            raise RuntimeError("Not OK")
        if ret[:-4]:
            return ret[:-4]
        return None

    async def _cmd_async(self, cmd):  # pylint: disable=too-many-branches
        async with self._cmd_lock:

            if len(cmd) > 127:
                raise ValueError("Command too long.")

            more = True
            pos = 0
            while len(cmd) - pos:
                if len(cmd) - pos <= 16:
                    more = False
                plen = len(cmd) - pos
                plen = min(plen, 16)
                self._create_sdep_raw(self._buf_tx, cmd[pos : pos + plen], more=more)
                pos += plen

                await asyncio.sleep(0.05)
                with self._spi_device as spi:
                    spi.write(self._buf_tx, end=len(cmd) + 4)  # pylint: disable=no-member

            timeout = 0.2
            while timeout > 0 and not self._irq.value:
                await asyncio.sleep(0.01)
                timeout -= 0.01
            if timeout <= 0:
                raise RuntimeError("Timed out waiting for a response.")

            msgtype = 0
            rspid = 0
            rsplen = 0
            rsp = b""
            while self._irq.value is True:
                await asyncio.sleep(0.01)
                with self._spi_device as spi:
                    spi.readinto(self._buf_rx)

                msgtype, rspid, rsplen = struct.unpack(">BHB", self._buf_rx[0:4])
                if rsplen >= 16:
                    rsp += self._buf_rx[4:20]
                else:
                    rsp += self._buf_rx[4 : rsplen + 4]

                await asyncio.sleep(0.05)

            return msgtype, rspid, rsp

    async def command_async(self, string):
        try:
            msgtype, msgid, rsp = self._cmd_async(string + "\n")
            if msgtype == _MSG_ERROR:
                raise RuntimeError("Error (id:{0})".format(hex(msgid)))
            if msgtype == _MSG_RESPONSE:
                return rsp
            raise RuntimeError("Unknown response (id:{0})".format(hex(msgid)))
        except RuntimeError as error:
            raise RuntimeError("AT command failure: " + repr(error)) from error

    async def command_async_check_OK(self, command, delay=0.0):  # pylint: disable=invalid-name
        ret = self.command(command)
        await asyncio.sleep(delay)
        if not ret or not ret[-4:]:
            raise RuntimeError("Not OK")
        if ret[-4:] != b"OK\r\n":
            raise RuntimeError("Not OK")
        if ret[:-4]:
            return ret[:-4]
        return None

    @property
    def connected(self):
        """Whether the Bluefruit module is connected to the central"""
        return int(self.command_check_OK(b"AT+GAPGETCONN")) == 1
