import badge
from micropython import mem_info
from machine import unique_id
import struct
import logging
import gc
import os
import utime
import asyncio
import time
print(f"Free memory before import: {gc.mem_free()} bytes")
gc.collect()  # Collect garbage to free up memory
print(f"Free memory after collect: {gc.mem_free()} bytes")
from ellipticcurve import PublicKey, Ecdsa, Signature
print(f"Free memory after imports: {gc.mem_free()} bytes")
gc.collect()  # Collect garbage again after imports
print(f"Free memory after second collect: {gc.mem_free()} bytes")

with open(badge.utils.get_data_dir() + "/announcement_key.txt", "r") as f:
    announcement_key_raw = f.read()
    vk = PublicKey.fromCompressed(announcement_key_raw)

# ANNOUNCEMENT FORMAT:
# 1 byte: reserved (should be 0)
# 32 bytes: r-value of the ECDSA signature of the rest of the message
# 32 bytes: s-value of the ECDSA signature
# 4 bytes: announcement creation time (Unix timestamp, also serves as announcement ID)
# 1 byte: length of the message, in bytes
# 179 bytes: message text, padded with null bytes
MSG_FMT = "!B32s32sIB179s"
SIGLESS_MSG_FMT = "!IB179s"

class Message:
    creation_timestamp: int
    message: str
    signature: Signature
    signature_valid: bool

    def __init__(self, creation_timestamp: int, message: str, signature: Signature) -> None:
        self.creation_timestamp = creation_timestamp
        self.message = message
        self.signature = signature
        self._signature_valid = None
    
    def is_signature_valid(self) -> bool:
        if self._signature_valid is not None:
            return self._signature_valid
        sigless_msg = struct.pack(SIGLESS_MSG_FMT, self.creation_timestamp, len(self.message), self.message.encode('utf-8') + b'\x00' * (195 - len(self.message)))
        self._signature_valid = Ecdsa.verify(sigless_msg, self.signature, vk)
        return self._signature_valid

    @classmethod
    def from_bytes(cls, data: bytes) -> 'Message':
        logger = logging.getLogger("Message.from_bytes")
        logger.setLevel(logging.DEBUG)
        logger.debug(f"free memory before decoding: {gc.mem_free()} bytes")
        gc.collect()  # Collect garbage before decoding
        logger.debug(f"free memory after collect: {gc.mem_free()} bytes")

        if len(data) != struct.calcsize(MSG_FMT):
            raise ValueError("Invalid message data length")
        reserved, sigr, sigs, creation_timestamp, length, message = struct.unpack(MSG_FMT, data)
        logger.debug(f"Unpacked data: reserved={reserved}, sigr={sigr.hex()}, sigs={sigs.hex()}, creation_timestamp={creation_timestamp}, length={length}, message={message}")
        if reserved != 0:
            logger.warning("Reserved byte is not zero, this badge is probably outdated")
        signature = Signature(int.from_bytes(sigr, 'big'), int.from_bytes(sigs, 'big'))
        try:
            decoded = message[:length].decode('utf-8').rstrip('\x00')  # Decode bytes to string and remove padding null bytes
        except UnicodeError:
            logger.error("Failed to decode message, it may be corrupted or not UTF-8 encoded")
            decoded = "message decode error"
            # hack so that message gets rejected as old
            creation_timestamp = 0
        
        # logger.debug(f"free memory after unpacking: {gc.mem_free()} bytes")
        # gc.collect()
        # logger.debug(f"free memory after second collect: {gc.mem_free()} bytes")
        # mem_info(True)

        # decoded = ''.join(chr(message[i]) for i in range(179))  # Convert bytes to string
        # print(f"Decoded message: {decoded}")
        # print(f"Free memory after decoding: {gc.mem_free()} bytes")
        # decoded = decoded.rstrip('\x00')  # Remove padding null bytes
        return cls(creation_timestamp, decoded, signature)  

    def to_bytes(self) -> bytes:
        """Convert the message to raw bytes"""
        reserved = 0
        length = len(self.message)
        if length > 195:
            raise ValueError("Message is too long")
        message_padded = self.message + '\x00' * (195 - length)  # Pad with null bytes
        message_bytes = message_padded.encode('utf-8')
        return struct.pack(MSG_FMT, reserved, self.signature, self.creation_timestamp, length, message_bytes)
    
    def __repr__(self) -> str:
        return f"Message(creation_timestamp={self.creation_timestamp}, message='{self.message}', signature_valid={self.is_signature_valid()}, signature={self.signature} (r={self.signature.r}, s={self.signature.s}))"

class App(badge.BaseApp):
    def __init__(self) -> None:
        self.last_button = False
        self.received_message = None

    def get_last_displayed_message_timestamp(self) -> int:
        try:
            with open(badge.utils.get_data_dir() + "/last_displayed_timestamp.txt", "r") as f:
                timestamp = int(f.read())
                return timestamp
        except Exception as e:
            self.logger.error(f"Failed to load last displayed timestamp: {e}")
            return 1
    
    def set_last_displayed_message_timestamp(self, timestamp: int) -> None:
        try:
            with open(badge.utils.get_data_dir() + "/last_displayed_timestamp.txt", "w") as f:
                f.write(str(timestamp))
        except Exception as e:
            self.logger.error(f"Failed to save last displayed timestamp: {e}")

    def get_last_received_message(self) -> Message:
        try:
            with open(badge.utils.get_data_dir() + "/last_message.bin", "rb") as f:
                data = f.read()
                if data:
                    message = Message.from_bytes(data)
                    self.logger.info(f"Loaded last packet from file: {message}")
                    return message
        except Exception as e:
            self.logger.error(f"Failed to load last packet from file: {e}")
        return None
    
    def on_open(self) -> None:
        message = self.get_last_received_message()
        if message.is_signature_valid():
            self.received_message = message

    def loop(self) -> None:
        # testing code, no longer needed
        # if badge.input.get_button(badge.input.Buttons.SW4):
        #     # TEST: decoding a message
        #     if not self.last_button:
        #         message_raw = b"\x00~\xbev\x04\xd6\x9b\x1aT\x97\xa9\x16\xe5s\x87\x17[<\x9b>\xd7\x03\x95\xe5H7\xd4\xa9\x8cb\x13\xe8/7\x01\xc7ah~\xa6\xb8\x10\xdf\x85Q\xfd\xeb\xf3\xb3`\x16\xf6\xdb.\xa7\xb2KD.\xc8\xb67\xca\x8a\xcfh\x95\xf5@\xb3This is a super long message to test how the word wrapper works. I'm just going to keep typing until I get cut off. Is this too long yet? It's difficult to guess at how long 179 c"
        #         self.on_packet(badge.radio.Packet(0xffff, 3, message_raw), True)
        #     self.last_button = True
        # else:
        #     self.last_button = False
        
        if self.received_message:
            self.logger.info(f"Displaying message: {self.received_message}")
            badge.display.fill(1)
            # word wrapping the message to fit in the display
            font_size = 24
            wrapped_message = self.wrap_message(self.received_message.message, font_size)
            if len(wrapped_message) > (200-70)//font_size:
                # if we can't make it work with size 24, try size 18
                font_size = 18
                wrapped_message = self.wrap_message(self.received_message.message, font_size)
            parsed_time = time.localtime(self.received_message.creation_timestamp - (4 * 3600))  # Convert to local time (UTC-4)
            title_size = 42 if font_size == 24 else 32
            badge.display.nice_text("Announced:", 0, 0, title_size)
            badge.display.nice_text(f"At:{parsed_time[3]:02}:{parsed_time[4]:02}:{parsed_time[5]:02} {self.num_to_weekday(parsed_time[6])}", 0, title_size + 1, font_size)
            badge.display.nice_text('\n'.join(wrapped_message), 0, title_size + 2 + font_size, font_size)
            badge.display.show()
            if self.should_display_message(self.received_message):
                asyncio.create_task(self.notify())
            self.set_last_displayed_message_timestamp(self.received_message.creation_timestamp)
            self.received_message = None

    def wrap_message(self, message: str, size: int) -> list[str]:
        max_chars_per_line = 16 if size == 24 else 25
        wrapped_message = [message[i:i + max_chars_per_line] for i in range(0, len(message), max_chars_per_line)]
        result = []
        for line in wrapped_message:
            result += line.split('\n')  # Split by newlines if any
        return result

    def num_to_weekday(self, num: int) -> str:
        """
        Convert a number to a weekday name.
        :param num: Number representing the day of the week (0=Monday, 6=Sunday).
        :return: Name of the weekday.
        """
        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return weekdays[num % 7]

    def save_message(self, messageBytes: bytes) -> None:
        with open(badge.utils.get_data_dir() + "/last_message.bin", "wb") as f:
            f.write(messageBytes)
        self.logger.info("Message saved to file")

    async def siren(self) -> None:
        """
        Siren the LED to indicate a new message.
        This async function runs on the OS thread - make sure it yields properly.
        """
        for i in range(0, 65535, 5000):
            badge.utils.set_led_pwm(i)
            await asyncio.sleep(0.05)
        badge.utils.set_led(True)
        for i in range(65535, 0, -5000):
            badge.utils.set_led_pwm(i)
            await asyncio.sleep(0.05)
        badge.utils.set_led_pwm(0)

    async def ring(self) -> None:
        """
        Ring the buzzer to indicate a new message.
        This async function runs on the OS thread - make sure it yields properly.
        """
        # siren the buzzer - for loop with audible tones
        badge.buzzer.tone(523, 0.5)  # C5
        await asyncio.sleep(0.1)
        badge.buzzer.tone(392, 0.25)  # G4
        await asyncio.sleep(0.05)
        badge.buzzer.tone(392, 0.25)  # G4
        await asyncio.sleep(0.05)
        badge.buzzer.tone(415, 0.5)  # G#4
        await asyncio.sleep(0.1)
        badge.buzzer.tone(392, 0.5)  # G4
        await asyncio.sleep(0.6)
        badge.buzzer.tone(493, 0.5)  # B4
        await asyncio.sleep(0.1)
        badge.buzzer.tone(523, 0.5)  # C5
        await asyncio.sleep(0.1)
        badge.buzzer.no_tone()

    async def notify(self) -> None:
        """
        Asynchronously notify the user of a new message.
        """

        # is this the right way to do this?
        await self.siren()
        await self.ring()
        await self.siren()

    def should_display_message(self, message: Message) -> bool:
        """
        Confirm that the message is newer than the last one we displayed,
        and that its signature is valid.
        """
        return message.creation_timestamp > self.get_last_displayed_message_timestamp() and message.is_signature_valid()
    
    def should_receive_message(self, message: Message) -> bool:
        """
        Confirm that the message is newer than the last one we received,
        and that its signature is valid.
        """
        last_message = self.get_last_received_message()
        if last_message is None:
            return message.is_signature_valid()
        return message.creation_timestamp > last_message.creation_timestamp and message.is_signature_valid()

    def on_packet(self, packet: badge.radio.Packet, is_foreground: bool) -> None:
        # NOTE to people looking at this for inspiration:
        # It is very bad behavior for most apps to forcibly
        # launch themselves from the background like this.
        # The announcements app is an exception because receiving
        # announcements is quite literally the primary function
        # of the Shipwrecked badge.
        # Again, your apps RFC2119-SHOULD-NOT do this.
        self.logger.info(f"Received message packet: {packet}")
        # verify it so we don't launch/update on a spoofed or old message
        message = Message.from_bytes(packet.data)
        if not self.should_receive_message(message):
            self.logger.info(f"Not receiving message: {message}")
            return
        # save the message
        self.save_message(packet.data)

        if not is_foreground:
            # launch the foreground app to display it
            from internal_os.internalos import InternalOS
            import asyncio
            internal_os = InternalOS.instance()
            asyncio.create_task(internal_os.apps.launch_app(internal_os.apps.get_current_app_repr()))
        else:
            self.logger.info(f"Received packet in foreground app")
            self.received_message = message