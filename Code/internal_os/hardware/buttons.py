from machine import I2C, Pin

try:
    from typing import List
except ImportError:
    # we're on an MCU, typing is not available
    pass

ADDRESS: int = 0x20  # I2C address of PCA9555
INPUT_PORT_0: int = 0x00
INPUT_PORT_1: int = 0x01
OUTPUT_PORT_0: int = 0x02
OUTPUT_PORT_1: int = 0x03
POL_INVERSION_PORT_0: int = 0x04
POL_INVERSION_PORT_1: int = 0x05
CONFIG_PORT_0: int = 0x06
CONFIG_PORT_1: int = 0x07

class BadgeButtons:
    """
    The class that manages the buttons on the badge.
    """
    interrupt_pin: Pin
    i2c: I2C
    button_states: List[bool]

    def __init__(self) -> None:
        # initialize rp2040 peripherals
        self.interrupt_pin = Pin(2, Pin.IN, Pin.PULL_UP) # open-drain, set when a pin changes state, cleared on read
        self.i2c = I2C(0, scl=Pin(1), sda=Pin(0))

        # initialize the PCA9555 I/O expander
        self.i2c.writeto_mem(ADDRESS, CONFIG_PORT_0, bytearray([0xff])) # set the bottom 8 pins as inputs
        self.i2c.writeto_mem(ADDRESS, CONFIG_PORT_1, bytearray([0xff])) # set the top 8 pins as inputs

        # initialize internal state
        self.button_states = [False] * 16  # 16 buttons, all initially not pressed

        # set up the interrupt handler
        self.interrupt_pin.irq(trigger=Pin.IRQ_FALLING, handler=self._update_button_states)

    def _read_raw_inputs(self) -> bytes:
        """
        Read the raw state of the input pins from the PCA9555.
        """
        return self.i2c.readfrom_mem(ADDRESS, INPUT_PORT_0, 2)
    
    def _update_button_states(self, _: object) -> None:
        """
        ISR: Update the button states based on the raw input data.
        """
        raw_data = self._read_raw_inputs()
        for i in range(16):
            # Check if the button is pressed (active low)
            self.button_states[i] = not (raw_data[i // 8] & (1 << (i % 8)))
    
    def is_pressed(self, button_index: int) -> bool:
        """
        Check if a specific button is pressed.
        :param button_index: Index of the button (0-15).
        :return: True if the button is pressed, False otherwise.
        """
        if 0 <= button_index < 16:
            return self.button_states[button_index]
        else:
            raise ValueError("Button index must be between 0 and 15.")
    
    def get_all_states(self) -> List[bool]:
        """
        Get the states of all buttons.
        :return: A list of boolean values representing the state of each button (True for pressed, False for not pressed).
        """
        return self.button_states.copy()
