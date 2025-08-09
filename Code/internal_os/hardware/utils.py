import logging
from machine import Pin, PWM, unique_id as machine_unique_id

CUSTOM_ID = 0x0000 # CHANGE THIS IF YOU WANT A CUSTOM BADGE ID
def unique_id():
    if CUSTOM_ID is not None:
        return CUSTOM_ID.to_bytes(2, 'big')
    else:
        return machine_unique_id()

class BadgeUtils:
    def __init__(self):
        self.logger = logging.getLogger("BadgeUtils")
        self.logger.setLevel(logging.DEBUG)
        self.led = Pin(16, Pin.OUT)
        self.set_led_pwm(0)

    def set_led(self, value: bool) -> None:
        """
        Set the LED state.
        :param value: True to turn on the LED, False to turn it off.
        """
        if value:
            self.set_led_pwm(65535)
            self.logger.info("LED turned ON")
        else:
            self.set_led_pwm(0)
            self.logger.info("LED turned OFF")

    def set_led_pwm(self, value: int) -> None:
        """
        Set the LED state.
        :param value: Control the brightness of the LED (0-65535).
        """
        pwm = PWM(self.led)
        pwm.freq(1000)
        pwm.duty_u16(value)
        self.logger.debug(f"LED PWM set to {value}")
