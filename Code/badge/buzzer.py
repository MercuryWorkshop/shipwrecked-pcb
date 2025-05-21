from internal_os.internalos import InternalOS
import utime

internal_os = InternalOS.instance()

def tone(frequency: float, length: float) -> None:
    """
    Play a tone on the buzzer.
    :param frequency: Frequency of the tone in Hz.
    :param length: Length of the tone in seconds.
    """
    if frequency <= 0 or length < 0:
        raise ValueError("Frequency must be positive and length must be non-negative.")

    # Set the buzzer frequency
    internal_os.buzzer.freq(int(frequency))
    
    # Start the buzzer
    internal_os.buzzer.duty_u16(32768)  # 50% duty cycle
    
    # Wait for the specified length
    utime.sleep(length)
    
    # Stop the buzzer
    internal_os.buzzer.duty_u16(0)  # Turn off the buzzer

def no_tone() -> None:
    """
    Stop any sound currently playing on the buzzer.
    """
    internal_os.buzzer.duty_u16(0)  # Turn off the buzzer