import os
from internal_os.internalos import InternalOS
import logging

internal_os = InternalOS.instance()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_data_dir() -> str:
    """
    Returns the path to the data directory.
    """
    app_path = internal_os.apps.get_current_app_repr().app_path
    app_name = app_path.split("/")[-1]
    result = f"/data/{app_name}"
    # create the directory if it doesn't exist
    try:
        _ = os.stat(result)
    except OSError:
        logger.info(f"Creating data directory: {result}")
        prefix = ""
        for part in result.split("/")[1:]:
            prefix += f"/{part}"
            try:
                logger.debug(f"Creating directory: {prefix}")
                os.mkdir(prefix)
            except OSError:
                # directory already exists, ignore
                logger.debug(f"Directory already exists: {prefix}")
                pass

    return result

def set_led(value: bool) -> None:
    """
    Set the LED state.
    :param value: True to turn on the LED, False to turn it off.
    """
    
    if value:
        internal_os.utils.set_led(True)
    else:
        internal_os.utils.set_led(False)

def set_led_pwm(value: int) -> None:
    """
    Set the LED state.
    :param value: Control the brightness of the LED (0-65535).
    """
    internal_os.utils.set_led_pwm(value)