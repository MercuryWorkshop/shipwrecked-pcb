""" Abstraction of the radio driver """
import asyncio
from machine import I2C, Pin
import time

try:
    from typing import List
except ImportError:
    # we're on an MCU, typing is not available
    pass

from sx1262 import SX1262
import logging

sx = SX1262(
    spi_bus=0,
    clk=18, mosi=19, miso=20,
    cs=21, irq=17, rst=23, gpio=22
)

class Packet:
    """
    Represents a packet.
    """
    def __init__(self, dest: int, app_number: int, data: bytes):
        if not isinstance(dest, int):
            raise TypeError("dest must be an integer")
        if not isinstance(app_number, int):
            raise TypeError("app_number must be an integer")
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes")
        self.source = int.from_bytes(unique_id()[-2:], 'big')  # source address from unique ID
        self.dest = dest
        self.app_number = app_number
        self.data = data

    def __repr__(self):
        return f"Packet(source={self.source:x}, dest={self.dest:x}, app_number={self.app_number}, data={self.data})"

    def to_dict(self):
        """
        Convert the contact to a dictionary representation.
        """
        return {
            'source': self.source,
            'dest': self.dest,
            'app_number': self.app_number,
            'data': self.data,
        }

class BadgeRadio:

    def __init__(self, internal_os) -> None:
        self.internal_os = internal_os
        self.logger = logging.getLogger("BadgeRadio")
        self.logger.setLevel(logging.DEBUG)

        self._receive_queue = []  # rx queue
        self._transmit_queue = [] # tx queue

        self.last_tx_time = time.ticks_ms()

        sx.begin(
            freq=923, bw=500.0, sf=7, cr=8, syncWord=0x12,
            power=22, currentLimit=140.0, preambleLength=8, # max power!
            implicit=False, implicitLen=0xFF,
            crcOn=True, txIq=False, rxIq=False,
            tcxoVoltage=0, useRegulatorLDO=False, # crystal, dcdc regulator
            blocking=False # used with a callback
        )
        sx.setBlockingCallback(False, self._lora_callback)

    def _lora_callback(self, events):
        if events & SX1262.RX_DONE:
            msg, status = sx.recv()
            self._handle_packet(msg)

    def _send_msg(self, dest: bytes, target_app: bytes, message: bytes):
        """
        Sends a message over LoRa.
        Takes in app ID, and optional message type. If ommited, it's an announcement.
        """

        """ bytes 0-1: source addr
        bytes 2-3: dest addr
        bytes 4-5: packet type
        bytes 6-254: app-specific payload """

        src_bytes = unique_id()[-2:]

        msg_bytes = bytearray(6 + len(message))
        msg_bytes[0:2] = src_bytes
        msg_bytes[2:4] = dest
        msg_bytes[4:6] = target_app
        msg_bytes[6:] = message
        self.logger.debug(f"Sending message: {msg_bytes}")

        sx.send(msg_bytes)

    def _handle_packet(self, packet) -> None:
        """
        Directs to target app API
        TODO: implement app dispatching in internal_os
        """
        if not packet or len(packet) < 6:
            logging.warning("Received malformed packet")
            return

        src = int.from_bytes(packet[0:2], 'big')
        dest = int.from_bytes(packet[2:4], 'big')
        target_app = int.from_bytes(packet[4:6], 'big')
        payload = packet[6:]

        pkt = Packet(dest, target_app, payload)
        pkt.source = src  # set source from packet

        if pkt.dest != int.from_bytes(unique_id()[-2:], 'big') and pkt.dest != 0xFFFF:
            logging.debug(f"Packet not for this badge: {pkt.dest:x} != {int.from_bytes(unique_id()[-2:], 'big'):x} or not broadcast")
            return

        self._receive_queue.append(pkt)  # add packet to the rx queue

        # dispatching is handled in manage_packets_forever

    def get_packets_available(self) -> int:
        """
        Returns the number of packets available in the receive queue.
        """
        return len(self._receive_queue)

    def get_next_packet(self):
        """
        Retrieves and removes the next packet from the receive queue.
        Returns None if the queue is empty.
        """
        if self._receive_queue:
            return self._receive_queue.pop(0)
        return None

    def get_send_queue_size(self) -> int:
        """
        Returns the number of packets in the send queue.
        """
        return len(self._transmit_queue)

    def get_time_to_next_send(self) -> float:
        """
        Returns the time in seconds until the next packet can be sent.
        """
        current_time = time.ticks_ms()
        elapsed_time = time.ticks_diff(current_time, self.last_tx_time)
        ms_per_packet = 1500
        return max(0, (ms_per_packet - elapsed_time) / 1000.0)

    def add_to_tx_queue(self, dest: int, app_number: int, data: bytes):
        """
        Adds a packet to the transmit queue.
        """
        pkt = Packet(dest, app_number, data)
        self._transmit_queue.append(pkt)
        logging.info(f"Added packet to transmit queue: {pkt}")

    async def manage_packets_forever(self):
        while True:
            # manage the transmission rate and dispatch packets
            if len(self._receive_queue) > 0:
                packet = self.get_next_packet()
                if packet:
                    logging.info(f"Dispatching packet: {packet}")
                    self.internal_os.apps.dispatch_packet(packet)

            if len(self._transmit_queue) > 0:
                # handle sending packets
                self.logger.debug(f"Transmit queue size: {len(self._transmit_queue)}")
                if self.get_time_to_next_send() <= 0:
                    pkt = self._transmit_queue.pop(0)
                    self.logger.debug(f"Sending packet: {pkt}")
                    self._send_msg(pkt.dest.to_bytes(2, 'big'), pkt.app_number.to_bytes(2, 'big'), pkt.data)
                    self.logger.info(f"Sent packet: {pkt}")
                    self.last_tx_time = time.ticks_ms()
                    logging.info(f"Sent packet: {pkt}")

            await asyncio.sleep(0.1)
