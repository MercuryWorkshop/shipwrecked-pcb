import logging
from machine import Pin, PWM

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