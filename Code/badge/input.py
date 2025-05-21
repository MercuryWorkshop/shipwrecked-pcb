try:
    from typing import List, TypeAlias
except ImportError:
    # we're on an MCU, typing is not available
    pass

import logging
logger = logging.getLogger("Buttons")

from internal_os.internalos import InternalOS

internal_os = InternalOS.instance()

Button: TypeAlias = int
class Buttons:
    """
    An enum of all the available buttons.
    """
    SW3: Button = 0
    SW4: Button = 1
    SW5: Button = 2
    SW6: Button = 3
    SW7: Button = 4
    SW8: Button = 5
    SW9: Button = 6
    SW10: Button = 7
    SW11: Button = 8
    SW12: Button = 9
    SW13: Button = 10
    SW14: Button = 11
    SW15: Button = 12
    SW16: Button = 13
    SW17: Button = 14
    SW18: Button = 15



def get_button(button: Button) -> bool:
    """
    Get the state of a button.
    :param button: The button to check.
    :return: True if the button is pressed, False otherwise.
    """
    if button == 0:
        logger.warning("Button 0 is the home button. Your application cannot access it. If you want to detect yourself being closed, implement the on_close function.")
    return internal_os.buttons.is_pressed(button)