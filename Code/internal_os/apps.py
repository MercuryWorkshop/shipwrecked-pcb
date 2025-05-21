try:
    from typing import List, Optional, Dict, TypeAlias
except ImportError:
    # we're on an MCU, typing is not available
    pass
import asyncio
import sys
from internal_os.baseapp import BaseApp
from internal_os.hardware.display import BadgeDisplay
from internal_os.hardware.buttons import BadgeButtons
from io import StringIO
from internal_os.hardware.radio import Packet
import logging
import os
import json
import _thread
import machine
import utime
from micropython import mem_info

class AppRepr:
    """
    This class represents a single app that is known to the badge. It may or may not be instantiated.
    """
    app_path: str
    display_name: str
    logo_path: str
    full_screen: bool
    suppress_notifs: bool
    permissions: List[str]
    radio_settings: Dict
    app_number: int

    @classmethod
    def from_json(cls, path: str, json_str: str) -> 'AppRepr':
        """
        Create an AppRepr instance from a JSON representation.
        :param json_data: The manifest representing the app.
        :return: An instance of AppRepr.
        """
        json_data = json.loads(json_str)
        app_repr = cls()
        app_repr.app_path = path
        app_repr.display_name = json_data.get("displayName", "")
        app_repr.logo_path = path + "/" + json_data.get("logoPath", "")
        app_repr.full_screen = json_data.get("fullScreen", False)
        app_repr.suppress_notifs = json_data.get("suppressNotifs", False)
        app_repr.permissions = json_data.get("permissions", [])
        app_repr.radio_settings = json_data.get("radioSettings", {})
        try:
            app_repr.app_number = int(json_data.get("appNumber", ""))
        except ValueError:
            raise ValueError(f"Invalid appNumber in manifest for {app_repr.display_name}. It must be an integer.")
        return app_repr

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, AppRepr):
            return NotImplemented
        return self.app_path == value.app_path


class TimeoutError(Exception):
    """
    Custom exception for timeout errors.
    """
    def __init__(self, message: str):
        super().__init__(message)

async def acquire_lock(lock: _thread.LockType, timeout: Optional[float] = None):
    """
    Acquire a lock asynchronously with an optional timeout.
    :param lock: The lock to acquire.
    :param timeout: Optional timeout in seconds.
    :return: True if the lock was acquired, False if timed out.
    """
    aquired = False
    start_time = utime.ticks_ms()
    while not aquired:
        if lock.acquire(0): # 0 means non-blocking
            aquired = True
        else:
            if timeout is not None:
                elapsed = utime.ticks_diff(utime.ticks_ms(), start_time)
                if elapsed >= timeout * 1000:
                    raise TimeoutError(f"Failed to acquire lock within {timeout} seconds.")
            await asyncio.sleep(0.1)  # Yield control to the event loop

def load_app(launch_logger: logging.Logger, app_repr: AppRepr) -> None:
    """
    import an app and make sure it's well-formed.
    """
    applib = __import__(app_repr.app_path + '.main', globals(), locals(), ['App'])
    launch_logger.debug(f"Imported app module: {app_repr.app_path}.main")
    # check that the app has an App class, and that that class descends from BaseApp
    if not hasattr(applib, 'App'):
        raise ImportError(f"App {app_repr.display_name} does not define an class named `App`.")
    app_class = applib.App
    if BaseApp not in app_class.__bases__: # cannot use issubclass because the reexport from badge changes its identity
        raise TypeError(f"App {app_repr.display_name} does not inherit from `badge.BaseApp`.")
    app_logger = logging.getLogger(app_repr.display_name)
    app_logger.setLevel(logging.DEBUG)
    app = app_class()
    app.logger = app_logger
    return app

def app_thread(app_repr: AppRepr, manager: 'AppManager') -> None:
    """
    The thread that runs the app. It should run synchronously.
    :param app_repr: The AppRepr instance representing the app to run.
    :param manager: The AppManager instance managing the app.
    """
    # set up logging
    launch_logger = logging.getLogger("AppLaunch-" + app_repr.display_name)
    launch_logger.setLevel(logging.DEBUG)
    launch_logger.info(f"Starting app: {app_repr.display_name} from {app_repr.app_path}")
    # Acquire the lock before running the app
    manager.fg_app_lock.acquire(1) # 1 means block until we get it
    launch_logger.debug(f"Acquired app lock")
    try:
        app = load_app(launch_logger, app_repr)
        manager.selected_app_instance = app
        app.on_open()  # pyright: ignore[reportAttributeAccessIssue] # on_open is defined in BaseApp which is confirmed in load_app
        while manager.fg_app_running:
            app.loop() # pyright: ignore[reportAttributeAccessIssue] # loop is defined in BaseApp which is confirmed in load_app
        launch_logger.info(f"App {app_repr.display_name} has finished running.")

    except Exception as e:
        launch_logger.exception(e, f"Error in {app_repr.display_name}:")
        # Display the error on the badge
        # TODO:
        try:
            filelike = StringIO()
            sys.print_exception(e, filelike)
            manager.display.fill(1)  # Clear the display
            manager.display.text(f"Error in {app_repr.display_name}:", 0, 0)
            linecount = 0
            for line in filelike.getvalue().splitlines():
                sublines = [line[i:i+25] for i in range(0, len(line), 25)]
                for subline in sublines:
                    manager.display.text(subline, 0, 10 + linecount * 10)
                    linecount += 1
            manager.display.show()
        except Exception as display_error:
            launch_logger.exception(display_error, f"Failed to display error on badge: {display_error}")
    finally:
        # Release the lock when done
        manager.fg_app_lock.release()

class AppManager:
    """
    The AppManager class is responsible for managing the apps on the badge.
    It handles app registration, loading, and execution.
    """
    def __init__(self, buttons: BadgeButtons, display: BadgeDisplay) -> None:
        self.logger = logging.getLogger("AppManager")
        self.logger.setLevel(logging.DEBUG)

        self.buttons = buttons
        self.display = display

        self.selected_fg_app: Optional[AppRepr] = None  # The currently selected app, if any
        self.selected_app_instance: Optional[BaseApp] = None  # The currently selected app class, if any
        self.fg_app_running: bool = False  # Whether an app should currently be running
        self.fg_app_lock: _thread.LockType = _thread.allocate_lock()
        self.bg_app_repr: Optional[AppRepr] = None  # The background app, if any

        self.backgrounded_apps: List[AppRepr] = []  # Apps that are running in the background

        self.registered_apps: List[AppRepr] = []
        self.scan_for_apps()
    
    def get_current_app_repr(self) -> AppRepr | None:
        """
        Get the AppRepr of the app that calls this, taking into account whether it's foreground or background.
        """
        if _thread.get_ident() == 2:
            # thread ident 2 = core 1 = foregrounded app
            # we can only rely on this because of the RP2040's implementation of get_ident():
            # https://github.com/micropython/micropython/blob/master/ports/rp2/mpthreadport.c#L123
            return self.selected_fg_app
        else:
            # we're running on core 0, so it's a background app
            return self.bg_app_repr

    def scan_for_apps(self) -> None:
        """
        Scan for apps in the system and register new ones.
        """
        self.logger.info("Scanning for apps...")
        app_dirs = ['/apps/' + d[0] for d in os.ilistdir('/apps') if d[1] == 0x4000]  # 0x4000 is the directory type
        known_apps = {app.app_path: app for app in self.registered_apps}
        for app_dir in app_dirs:
            if app_dir not in known_apps:
                manifest_path = app_dir + '/manifest.json'
                self.logger.debug(f"Checking for manifest in {manifest_path}")
                try:
                    with open(manifest_path, 'r') as f:
                        json_data = f.read()
                        app_repr = AppRepr.from_json(app_dir, json_data)
                        self.registered_apps.append(app_repr)
                        self.logger.info(f"Registered app: {app_repr.display_name} from {app_dir}")
                        if app_repr.display_name.strip() == "":
                            self.logger.warning(f"App in {app_dir} has no display name. Please fix the manifest.")
                        # check if app logo path exists
                        try:
                            with open(app_repr.logo_path, 'rb') as logo_file:
                                pass
                        except OSError as e:
                            self.logger.warning(f"App {app_repr.display_name} in {app_dir} has a logo path that does not exist: {app_repr.logo_path}. Please fix the manifest. Error: {e}")
                            app_repr.logo_path = "/missingtex.pbm"

                        # TODO: add addl checks for things like paths existing, etc.
                except OSError as e:
                    self.logger.error(f"Failed to read manifest for app in {app_dir}. Skipping. Error: {e}")
                # except json.JSONDecodeError as e:
                #     self.logger.error(f"Invalid JSON in manifest for app in {app_dir}. Skipping. Error: {e}")
                except Exception as e:
                    self.logger.error(f"Unexpected error while registering app in {app_dir}. Skipping. Error: {e}")

        for known_app_dir in known_apps.keys():
            if known_app_dir not in app_dirs:
                # App has been removed
                self.registered_apps.remove(known_apps[known_app_dir])
                self.logger.info(f"Removed app: {known_app_dir}")
    
    async def scan_forever(self, interval: float = 5.0) -> None:
        """
        Continuously scan for apps at a specified interval.
        :param interval: Time in seconds between scans.
        """
        while True:
            self.scan_for_apps()
            await asyncio.sleep(interval)
    
    async def launch_app(self, app_repr: AppRepr) -> None:
        """
        Launch the specified app.
        :param app_repr: The AppRepr instance representing the app to launch.
        """
        if self.fg_app_running:
            # we need to stop the currently running app first
            self.fg_app_running = False
            self.logger.info(f"Stopping currently running app: {self.selected_fg_app.display_name if self.selected_fg_app else 'None'}")
            # The app should see that it's supposed to stop because app_running is set to False.
            # we'll know when that happens because it will release the app_lock.
            try:
                await acquire_lock(self.fg_app_lock, timeout=5.0)
            except TimeoutError as e:
                self.logger.critical(f"Failed to stop the currently running app within timeout: {e}")
                self.logger.critical(f"Soft-resetting the badge in order to recover.")
                self.logger.critical(f"This is caused by a bug in {self.selected_fg_app.display_name if self.selected_fg_app else 'the currently running app'} (usually an infinite loop).")
                self.logger.critical(f"Please report this bug to the app's developers.")
                machine.soft_reset()  # Reset the badge to recover from the stuck app
                return
            # once we have it, we can release it - the app thread should have stopped itself
            self.fg_app_lock.release()
        
        # Now we can start the new app
        self.selected_fg_app = app_repr
        self.logger.info(f"Creating app thread for: {app_repr.display_name} from {app_repr.app_path}")
        self.fg_app_running = True
        # mem_info(True)
        _thread.stack_size(8192)  # Set a larger stack size for the app thread
        _thread.start_new_thread(app_thread, (app_repr, self))
    
    def get_app_by_path(self, app_path: str) -> Optional[AppRepr]:
        """
        Get an app by its path.
        :param app_path: The path of the app to find.
        :return: The AppRepr instance if found, None otherwise.
        """
        for app in self.registered_apps:
            if app.app_path == app_path:
                return app
        return None
    
    def dispatch_packet(self, packet: Packet) -> None:
        """
        Dispatch a packet to an app, waking it if necessary.
        """
        self.logger.debug(f"Dispatching packet to app: {packet.app_number}")
        if self.selected_fg_app and self.selected_fg_app.app_number == packet.app_number:
            self.logger.debug(f"Packet for currently running app {self.selected_fg_app.display_name}.")
            self.bg_app_repr = self.selected_fg_app
            try:
                self.selected_app_instance.on_packet(packet, True)
            except Exception as e:
                self.logger.exception(e, f"Error while handling packet in {self.selected_fg_app.display_name}:")
                # TODO: display error on badge?
            finally:
                self.bg_app_repr = None
                self.logger.debug(f"Packet handled for app {self.selected_fg_app.display_name}.")
        else:
            # we need to load the app and run it in the background
            self.logger.debug(f"Packet for app {packet.app_number} not currently running. Loading it.")
            self.bg_app_repr = None
            for app in self.registered_apps:
                if app.app_number == packet.app_number:
                    self.bg_app_repr = app
                    self.logger.debug(f"Found app {self.bg_app_repr.display_name} for number {packet.app_number}.")
                    break
            if self.bg_app_repr is None:
                self.logger.error(f"App with app_number {packet.app_number} not found. Cannot dispatch packet: {packet}")
                return

            bg_launch_logger = logging.getLogger("BackgroundAppLaunch-" + self.bg_app_repr.display_name)
            bg_launch_logger.setLevel(logging.DEBUG)
            bg_launch_logger.info(f"Launching app {self.bg_app_repr.display_name} in background for packet handling.")
            try:
                app = load_app(bg_launch_logger, self.bg_app_repr)
                app.on_packet(packet, False)  # Handle the packet
                bg_launch_logger.info(f"App {self.bg_app_repr.display_name} handled packet successfully.")
            except Exception as e:
                bg_launch_logger.exception(e, f"Error while handling packet in background app {self.bg_app_repr.display_name}:")
            finally:
                self.bg_app_repr = None

    async def home_button_watcher(self) -> None:
        """
        Watch for the home button press and handle it.
        This will stop the currently running app and return to the home screen.
        """
        while True:
            await asyncio.sleep(0.1)
            if self.buttons.is_pressed(0) and self.fg_app_running:  # Assuming button 0 is the home button
                self.logger.info("Home button pressed. Stopping current app and launching home-screen.")
                home_app = self.get_app_by_path('/apps/home-screen')
                if not home_app:
                    self.logger.error("Home app not found. Cannot return to home screen.")
                    continue
                await self.launch_app(home_app)

