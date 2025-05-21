from internal_os.internalos import BadgeUART
from internal_os.internalos import InternalOS
internal_os = InternalOS.instance()

def present() -> bool:
    """
    Check if the UART is present.
    :return: True if the UART is present, False otherwise.
    """
    return internal_os.uart.detect_badge()

def try_connect() -> bool:
    """
    Try to connect to the UART.
    :return: True if the connection was successful, False otherwise.
    """
    return internal_os.uart.try_connect()

def is_connected() -> bool:
    """
    Check if the UART is connected.
    :return: True if the UART is connected, False otherwise.
    """
    return internal_os.uart.is_connected()

def send(data: bytes) -> None:
    """
    Send data over the UART.
    :param data: The data to send.
    :raises RuntimeError: If the UART is not connected.
    """
    internal_os.uart.send(data)

def receive(num_bytes: int) -> bytes:
    """
    Receive data from the UART.
    :return: The received data.
    :raises RuntimeError: If the UART is not connected.
    :param num_bytes: The number of bytes to read. Optional.
    """
    if not internal_os.uart.is_connected():
        raise RuntimeError("UART is not connected.")

    return internal_os.uart.read(num_bytes)# if num_bytes else internal_os.uart.read()