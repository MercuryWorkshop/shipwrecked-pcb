import _thread
import asyncio
import gc

from machine import RTC, Pin, PWM, unique_id

from internal_os.hardware.uart import BadgeUART
from internal_os.hardware.display import BadgeDisplay
from internal_os.hardware.buttons import BadgeButtons
from internal_os.hardware.radio import BadgeRadio
from internal_os.hardware.utils import BadgeUtils

from internal_os.contacts import ContactsManager
from internal_os.notifs import NotifManager
from internal_os.apps import AppManager

import logging

logging.basicConfig(level=logging.DEBUG)

# enable error reports for errors in ISRs
import micropython
micropython.alloc_emergency_exception_buf(100)

class InternalOS:
    """
    The class that manages the badge. It runs across two cores. The main core manages background tasks and runs with asyncio. The second core runs the app thread (synchronously).
    To start the badge, initialize the class, then call badge.start().
    To allow access from various contexts, this class is a singleton.
    """
    
    @classmethod
    def instance(cls):
        """
        Returns the singleton instance of InternalOS.
        If it doesn't exist, creates a new one.
        """
        if not hasattr(cls, '_instance'):
            cls._instance = cls()
        return cls._instance
    
    def start(self):
        self.setup()
        print("Badge started. Running forever...")
        self.run_forever()
    
    def setup(self):
        """
        Starts the badge. Never returns.
        """
        # To do in this function:
        # 1. Initialize hardware, IRQs, state, etc.
        # 2. Schedule the needed background tasks.
        # 3. Start the asyncio event loop.
    
        # Step 1:
        # hardware
        self.display = BadgeDisplay()
        self.radio = BadgeRadio(self)
        self.buttons = BadgeButtons()
        self.rtc = RTC()
        self.buzzer = PWM(Pin(28, Pin.OUT))
        self.utils = BadgeUtils()
        self.uart = BadgeUART()

        # software
        gc.enable()
        self.contacts = ContactsManager(self)
        self.notifs = NotifManager()
        self.apps = AppManager(self.buttons, self.display)


        # Step 2:
        asyncio.create_task(self.apps.scan_forever(interval=15)) # TODO: lower this interval in prod?
        asyncio.create_task(self.apps.home_button_watcher())
        asyncio.create_task(self.display.idle_when_inactive())
        asyncio.create_task(self.radio.manage_packets_forever())
        asyncio.create_task(self.launch_home_screen())

    def run_forever(self):
        # Step 3:
        asyncio.run(self.run_async())
        print("Forever is done")

    async def run_async(self):
        """
        The main async loop for the badge. This runs on the main core.
        """
        while True:
            await asyncio.sleep(1)

    async def launch_home_screen(self):
        """
        Launches the home screen app.
        This is the app that is shown when the badge is started.
        """
        await asyncio.sleep(1)  # Give time for the display to initialize
        home_app = self.apps.get_app_by_path('/apps/home-screen')
        if not home_app:
            self.apps.logger.error("Home app not found. Cannot launch home screen.")
            return
        await self.apps.launch_app(home_app)

    def get_badge_id_hex(self) -> str:
        """
        Returns the badge ID as a hex string.
        The badge ID is the last 2 bytes (4 digits) of the machine.unique_id().
        """
        return unique_id().hex()[-4:]
    
    def get_badge_id_int(self) -> int:
        return int.from_bytes(unique_id()[-2:], 'big')