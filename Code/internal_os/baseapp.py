from internal_os.hardware.radio import Packet
import logging

class BaseApp:
    """
    An abstract class that applications must inherit from.
    """
    logger: logging.Logger # set up by the app launcher
    def on_open(self) -> None:
        """
        Run once when the app is launched.
        This method should be overridden by the app.
        """
        raise NotImplementedError("on_open must be implemented by the app.")
    
    def loop(self) -> None:
        """
        The main loop of the app.
        Called repeatedly while the app is running.
        """
        raise NotImplementedError("loop must be implemented by the app.")
    
    def on_wake_from_lpm(self) -> None:
        """
        Called when the app is woken from low power mode.
        This method should be overridden by the app if needed.
        """
        pass

    def before_close(self) -> None:
        """
        Called before the app is closed. Should e.g. save state to the FS if needed.
        Has an enforced 200ms limit.
        This method should be overridden by the app if needed.
        """
        pass

    def on_packet(self, packet: Packet, in_foreground: bool) -> None:
        """
        Called when a packet is received while the app is running.
        This method should be overridden by the app if it needs to handle packets.
        NOTE: THIS FUNCTION DOES NOT RUN ON THE SAME THREAD AS THE APP'S MAIN LOOP.
        Treat this like an interrupt handler: be quick and be mindful of concurrency.
        """
        raise NotImplementedError(f"The app {self.__class__.__name__} (running in the {'foreground' if in_foreground else 'background'}) received a packet: {packet}, but does not implement on_packet.")