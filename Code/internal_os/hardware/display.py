from machine import Pin, SPI
from internal_os.hardware.einkdriver import EPD
import logging
import utime
import asyncio
import _thread 

class LockWrapper:
    """
    Allows use of a _thread lock as a context manager.
    Usage: ```python
    lock = _thread.allocate_lock()
    with LockWrapper(lock, timeout=5.0):
        # critical section code here
    ```
    """

    def __init__(self, lock, timeout=3.0):
        self.lock = lock
        self.timeout = timeout
        self.logger = logging.getLogger("LockWrapper")
        self.logger.setLevel(logging.INFO)
    
    def get_lock_or_error(self):
        """Acquire the display lock or raise an error if it times out"""
        self.logger.debug(f"Acquiring display lock (timeout={self.timeout}s) from thread {_thread.get_ident()}")
        start_time = utime.ticks_ms()
        while not self.lock.acquire(0):
            if utime.ticks_diff(utime.ticks_ms(), start_time) > self.timeout * 1000:
                raise RuntimeError(f"Failed to acquire display lock within timeout period. In other words, the other thread has grabbed it and is busy for some reason. (Raised from thread {_thread.get_ident()})")
            utime.sleep(0.01)
        self.logger.debug(f"Display lock acquired from thread {_thread.get_ident()}")

    def __enter__(self):
        """Enter the context manager, acquiring the lock."""
        self.get_lock_or_error()
        return self.lock
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager, releasing the lock."""
        self.lock.release()
        if exc_type is not None:
            self.logger.error(f"Exception in display lock context: {exc_val}")

class BadgeDisplay:
    """
    Manages the display. 
    TODO: make this and einkdriver async
    TODO: add partial refresh support
    TODO: if app is not in fullscreen mode, give it a smaller framebuffer and blit it over the main framebuffer
    """
    def __init__(self):
        IS_REAL_BADGE = True  # Set to False for testing on a breadboarded version
        self.logger = logging.getLogger("BadgeDisplay")
        self.logger.setLevel(logging.INFO)
        self.logger.info(f"Initializing BadgeDisplay ({'Real Badge' if IS_REAL_BADGE else 'Breadboarded Badge'})")
        # initialize rp2040 peripherals
        self.spi = SPI(0, baudrate=1_000_000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(19), miso=Pin(20))
        self.cs = Pin(24 if IS_REAL_BADGE else 13, Pin.OUT)
        self.dc = Pin(25 if IS_REAL_BADGE else 12, Pin.OUT)
        self.rst = Pin(26, Pin.OUT)
        self.busy = Pin(27, Pin.IN)

        self.display = EPD(self.spi, self.cs, self.dc, self.rst, self.busy)
        self.display.init()
        self.display.sleep()
        
        self.last_action = utime.ticks_ms()
        self.is_asleep = True
        self.display_lock = _thread.allocate_lock()
    
    async def idle_when_inactive(self):
        while True:
            current_time = utime.ticks_ms()
            if utime.ticks_diff(current_time, self.last_action) > 5000 and not self.is_asleep:
                try:
                    self.logger.info(f"No activity detected, putting display to sleep")
                    self.sleep_disp()
                    self.logger.debug(f"Display is now asleep (self.is_asleep={self.is_asleep}) from thread {_thread.get_ident()}")
                except NotImplementedError as e:
                    self.logger.error(f"Display sleep not implemented: {e}")
            await asyncio.sleep(0.5)
    
    def reset_idle_timer(self):
        """Reset the idle timer to prevent the display from sleeping for another 5 seconds"""
        self.is_asleep = False
        self.logger.debug(f"Resetting idle timer from thread {_thread.get_ident()} (self.is_asleep={self.is_asleep})")
        self.last_action = utime.ticks_ms()

    def show(self):
        """Push the contents of the internal framebuffer to the display"""
        self.reset_idle_timer()
        with LockWrapper(self.display_lock):
            self.display.display()
        self.reset_idle_timer()

    def sleep_disp(self):
        """Put the display to sleep to save power"""
        with LockWrapper(self.display_lock):
            self.display.sleep()
            self.is_asleep = True
            self.logger.debug(f"Display put to sleep from thread {_thread.get_ident()} (self.is_asleep={self.is_asleep})")
    
    def fill(self, color):
        """Fill the entire buffer with a color (0=black, 1=white)"""
        self.display.fill(color)
    
    def pixel(self, x, y, color):
        """Set a pixel color (0=black, 1=white)"""
        self.display.pixel(x, y, color)
    
    def hline(self, x, y, w, color):
        """Draw a horizontal line"""
        self.display.hline(x, y, w, color)
    
    def vline(self, x, y, h, color):
        """Draw a vertical line"""
        self.display.vline(x, y, h, color)
    
    def line(self, x1, y1, x2, y2, color):
        """Draw a line"""
        self.display.line(x1, y1, x2, y2, color)

    def rect(self, x, y, w, h, color):
        """Draw a rectangle"""
        self.display.rect(x, y, w, h, color)
    
    def fill_rect(self, x, y, w, h, color):
        """Draw a filled rectangle"""
        self.display.fill_rect(x, y, w, h, color)
    
    def text(self, text, x, y, color=0):
        """Draw text"""
        self.display.text(text, x, y, color)
    
    def blit(self, fb, x, y):
        """Blit a framebuffer onto the display"""
        self.display.blit(fb, x, y)