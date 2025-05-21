from machine import I2C, Pin, UART, unique_id
import logging
import asyncio

try:
    from typing import List
except ImportError:
    # we're on an MCU, typing is not available
    pass

class BadgeUART:
    def __init__(self) -> None:
        self.logger = logging.getLogger("BadgeUART")
        self.logger.setLevel(logging.DEBUG)
        self.uart_detect = Pin(3, Pin.IN, Pin.PULL_UP)
        self.uart = UART(1, baudrate=115200, tx=4, rx=5)
        self._uart_connected = False
        self._buffer = b''

    def detect_badge(self) -> bool:
        try:
            return not self.uart_detect.value()
        except Exception as e:
            self.logger.error(f"Error checking UART presence: {e}")
            return False
        
    def try_connect(self) -> bool:
        if self.detect_badge():
            self.logger.info("Badge UART detected. Attempting to connect...")
            try:
                self.uart.init(bits=8, parity=None, stop=2)
                self.uart.irq(handler=lambda uart: self._on_uart_rx(uart), trigger=UART.IRQ_RXIDLE)
                self.logger.info("Badge UART connection successful.")
                self._uart_connected = True
            except Exception as e:
                self.logger.error(f"Failed to initialize UART: {e}")
                return False
            return True
        else:
            self.logger.warning("Badge UART not detected.")
            return False
        
    def is_connected(self) -> bool:
        return self._uart_connected
    
    def send(self, data: bytes) -> None:
        if not self.is_connected():
            raise RuntimeError("UART is not connected.")
        self.uart.write(data)
        self.logger.debug(f"Sent data: {data}")

    def read(self, num_bytes: int) -> bytes:
        if not self.is_connected():
            raise RuntimeError("UART is not connected.")
        if self._buffer:
            data = self._buffer[:num_bytes]
            self._buffer = self._buffer[num_bytes:]
            return data
        return b''

    def _on_uart_rx(self, uart):
        """
        IRQ handler that is called when UART data is received.
        """
        if uart.any():
            data = uart.read()
            if data:
                self._buffer += data
                self.logger.debug(f"Received data: {data}, Buffer: {self._buffer}")

                # Check for 'ADDR' command
                if b'ADDR' in self._buffer:
                    self.logger.info("Received ADDR command, sending placeholder...")
                    #self.send(b'ADDR_ACK')
                    # Remove command from buffer to avoid reprocessing
                    self._buffer = self._buffer.replace(b'ADDR', b'')
