import utime
import time
from internal_os.internalos import InternalOS

def monotonic():
    """
    Returns the number of seconds since the system was started.
    This is a monotonic clock, meaning it will not go backwards.
    """
    return utime.ticks_ms() / 1000.0

def get_epoch_time():
    """
    Returns the current time in seconds since the epoch. NOTE: THIS IS NOT THE UNIX EPOCH!
    Micropython's epoch is 2000-01-01T00:00:00Z.
    This is a non-monotonic clock, meaning it can go backwards if the system time is changed.
    This clock is not guaranteed to have sub-second precision.
    """
    return time.time()

def set_epoch_time(epoch_time: int) -> None:
    """
    Sets the current time in seconds since the epoch. NOTE: THIS IS NOT THE UNIX EPOCH!
    Micropython's epoch is 2000-01-01T00:00:00Z.
    :param epoch_time: The time in seconds since the epoch to set.
    """
    if epoch_time < 0:
        raise ValueError("epoch_time must be a positive integer.")
    if not isinstance(epoch_time, int):
        raise TypeError("epoch_time must be an integer.")

    # Set the time using the time module
    time_tuple = time.localtime(epoch_time)
    internal_os = InternalOS.instance()
    internal_os.rtc.datetime(time_tuple)

