
"""
MicroPython driver for the Semtech SX1262 LoRa transceiver.
"""

from machine import Pin, SPI
import utime

# SX1262 commands
SET_SLEEP = 0x84
SET_STANDBY = 0x80
SET_FS = 0xC1
SET_TX = 0x83
SET_RX = 0x82
SET_CAD = 0xC5
SET_LORA_SYNC_WORD = 0x74
SET_PACKET_TYPE = 0x8A
SET_RF_FREQUENCY = 0x86
SET_PA_CONFIG = 0x95
SET_TX_PARAMS = 0x8E
SET_BUFFER_BASE_ADDRESS = 0x8F
SET_LORA_PACKET_PARAMS = 0x8C
SET_DIO_IRQ_PARAMS = 0x8D
GET_IRQ_STATUS = 0x12
CLEAR_IRQ_STATUS = 0x02
GET_PACKET_STATUS = 0x14
GET_RX_BUFFER_STATUS = 0x13
GET_STATUS = 0xC0
WRITE_REGISTER = 0x0D
READ_REGISTER = 0x1D
WRITE_BUFFER = 0x0E
READ_BUFFER = 0x1E

# Packet types
PACKET_TYPE_LORA = 0x01
PACKET_TYPE_GFSK = 0x00

# Standby modes
STDBY_RC = 0x00
STDBY_XOSC = 0x01

# Ramp times
RADIO_RAMP_10U = 0x00
RADIO_RAMP_20U = 0x01
RADIO_RAMP_40U = 0x02
RADIO_RAMP_80U = 0x03
RADIO_RAMP_200U = 0x04
RADIO_RAMP_800U = 0x05
RADIO_RAMP_1700U = 0x06
RADIO_RAMP_3400U = 0x07

# Spreading factors
LORA_SF5 = 0x05
LORA_SF6 = 0x06
LORA_SF7 = 0x07
LORA_SF8 = 0x08
LORA_SF9 = 0x09
LORA_SF10 = 0x0A
LORA_SF11 = 0x0B
LORA_SF12 = 0x0C

# Bandwidths
LORA_BW_7 = 0x00
LORA_BW_10 = 0x08
LORA_BW_15 = 0x01
LORA_BW_20 = 0x09
LORA_BW_31 = 0x02
LORA_BW_41 = 0x0A
LORA_BW_62 = 0x03
LORA_BW_125 = 0x04
LORA_BW_250 = 0x05
LORA_BW_500 = 0x06

# Coding rates
LORA_CR_4_5 = 0x01
LORA_CR_4_6 = 0x02
LORA_CR_4_7 = 0x03
LORA_CR_4_8 = 0x04

# IRQ flags
IRQ_TX_DONE = 1 << 0
IRQ_RX_DONE = 1 << 1
IRQ_PREAMBLE_DETECTED = 1 << 2
IRQ_SYNC_WORD_VALID = 1 << 3
IRQ_HEADER_VALID = 1 << 4
IRQ_HEADER_ERR = 1 << 5
IRQ_CRC_ERR = 1 << 6
IRQ_CAD_DONE = 1 << 7
IRQ_CAD_DETECTED = 1 << 8
IRQ_TIMEOUT = 1 << 9

class SX1262:
    def __init__(self, spi, cs, busy, dio1, rst):
        self.spi = spi
        self.cs = cs
        self.busy = busy
        self.dio1 = dio1
        self.rst = rst

        self.cs.init(self.cs.OUT, value=1)
        self.rst.init(self.rst.OUT, value=1)
        self.busy.init(self.busy.IN)
        self.dio1.init(self.dio1.IN)

        self.reset()
        self.standby(STDBY_RC)
        self.set_packet_type(PACKET_TYPE_LORA)

    def _read(self, command, length):
        self.cs.value(0)
        self.spi.write(bytearray([command]))
        data = self.spi.read(length)
        self.cs.value(1)
        return data

    def _write(self, command, data):
        self.cs.value(0)
        self.spi.write(bytearray([command]) + data)
        self.cs.value(1)

    def _wait_on_busy(self):
        while self.busy.value() == 1:
            utime.sleep_ms(1)

    def reset(self):
        self.rst.value(0)
        utime.sleep_ms(10)
        self.rst.value(1)
        utime.sleep_ms(10)
        self._wait_on_busy()

    def standby(self, mode):
        self._write(SET_STANDBY, bytearray([mode]))

    def sleep(self):
        self._write(SET_SLEEP, bytearray([0x00]))

    def set_packet_type(self, type):
        self._write(SET_PACKET_TYPE, bytearray([type]))

    def set_frequency(self, freq):
        freq_val = int((freq * (2**25)) / 32000000)
        self._write(SET_RF_FREQUENCY, freq_val.to_bytes(4, 'big'))

    def set_tx_params(self, power, ramp_time):
        self._write(SET_TX_PARAMS, bytearray([power, ramp_time]))

    def set_buffer_base_address(self, tx_base, rx_base):
        self._write(SET_BUFFER_BASE_ADDRESS, bytearray([tx_base, rx_base]))

    def set_lora_packet_params(self, header_type, spreading_factor, bandwidth, coding_rate, preamble_length, crc_type):
        self._write(SET_LORA_PACKET_PARAMS, bytearray([
            preamble_length >> 8, preamble_length & 0xFF,
            header_type,
            spreading_factor,
            bandwidth,
            coding_rate,
            crc_type
        ]))

    def set_dio_irq_params(self, irq_mask, dio1_mask, dio2_mask, dio3_mask):
        self._write(SET_DIO_IRQ_PARAMS, bytearray([
            irq_mask >> 8, irq_mask & 0xFF,
            dio1_mask >> 8, dio1_mask & 0xFF,
            dio2_mask >> 8, dio2_mask & 0xFF,
            dio3_mask >> 8, dio3_mask & 0xFF,
        ]))

    def get_irq_status(self):
        return int.from_bytes(self._read(GET_IRQ_STATUS, 2), 'big')

    def clear_irq_status(self, mask):
        self._write(CLEAR_IRQ_STATUS, bytearray([mask >> 8, mask & 0xFF]))

    def send(self, data):
        self.standby(STDBY_RC)
        self.set_buffer_base_address(0, 0)
        self._write(WRITE_BUFFER, bytearray([0]) + data)
        self.set_lora_packet_params(0x00, LORA_SF7, LORA_BW_125, LORA_CR_4_5, 8, 0x01)
        self.set_dio_irq_params(IRQ_TX_DONE, IRQ_TX_DONE, 0, 0)
        self._write(SET_TX, bytearray([0, 0, 0])) # Timeout = 0 (no timeout)

    def recv(self, timeout=0):
        self.standby(STDBY_RC)
        self.set_buffer_base_address(0, 0)
        self.set_lora_packet_params(0x00, LORA_SF7, LORA_BW_125, LORA_CR_4_5, 8, 0x01)
        self.set_dio_irq_params(IRQ_RX_DONE | IRQ_TIMEOUT, IRQ_RX_DONE | IRQ_TIMEOUT, 0, 0)
        timeout_val = int(timeout * 1000 / 15.625)
        self._write(SET_RX, bytearray([timeout_val >> 16, (timeout_val >> 8) & 0xFF, timeout_val & 0xFF]))

        while True:
            irq = self.get_irq_status()
            if irq & IRQ_RX_DONE:
                self.clear_irq_status(IRQ_RX_DONE)
                rx_status = self._read(GET_RX_BUFFER_STATUS, 2)
                length = rx_status[0]
                offset = rx_status[1]
                self._write(WRITE_REGISTER, bytearray([0x01, 0x0D, offset])) # Set buffer pointer
                payload = self._read(READ_BUFFER, length)
                return payload
            if irq & IRQ_TIMEOUT:
                self.clear_irq_status(IRQ_TIMEOUT)
                return None
            utime.sleep_ms(10)
