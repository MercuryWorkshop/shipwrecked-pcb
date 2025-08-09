import gc # Keep gc for explicit collection if needed later, but remove logging.
import math # math will be used by Celeste.py

# Define constants for button indices to avoid magic numbers and potential dictionary lookups
# in a loop, though MicroPython usually optimizes integer constants.
K_LEFT = 0
K_RIGHT = 1
K_UP = 2
K_DOWN = 3
K_JUMP = 4
K_DASH = 5

class PICO8():
  def __init__(self, cart):
    self._btn_state = 0
    # Initialize _memory with default empty map and flags.
    # These will be replaced by the game's actual data upon load_game.
    self._memory = {
      'map': bytearray(128 * 128), # Assuming a 128x128 map, initialized to zeros
      'flags': bytearray(256),    # Assuming 256 possible tile flags
    }
    self.load_game(cart)

  # game functions

  def btn(self, i):
    """
    Checks if a button is pressed.
    i: Index of the button (0-5)
    Returns True if button is pressed, False otherwise.
    Optimized: Uses bitwise operations directly.
    """
    return (self._btn_state & (1 << i)) != 0

  def mset(self, x, y, tile):
    """
    Sets a tile in the map memory.
    x, y: Tile coordinates (integer, not fixed-point pixels)
    tile: Tile ID
    Optimized: Direct bytearray access for speed.
    """
    # Map coordinates are already integer, so no fixed-point conversion needed here
    self._memory['map'][x + y * 128] = tile

  def mget(self, x, y):
    """
    Gets a tile from the map memory.
    x, y: Tile coordinates (integer, not fixed-point pixels)
    Returns the tile ID.
    Optimized: Direct bytearray access for speed.
    """
    # Map coordinates are already integer, so no fixed-point conversion needed here
    return self._memory['map'][x + y * 128]

  def fget(self, n, f=None):
    """
    Gets a flag for a tile.
    n: Tile ID
    f: Flag index (0-7). If None, returns all flags for the tile.
    Optimized: Direct bytearray access and bitwise operations.
    """
    flags = self._memory['flags'][n]
    return flags if f is None else (flags & (1 << f)) != 0

  # console commands

  def load_game(self, cart):
    """
    Loads a new game (cartridge) into the PICO-8 emulator.
    Initializes game state and memory.
    """
    self._cart = cart
    # Instantiate the game, passing self (PICO8 instance) to it
    self._game = self._cart(self)
    
    # Retrieve map and flag data from the game instance.
    # Assuming _game.map_data and _game.flag_data are efficient bytearray properties.
    self._memory['map'] = self._game.map_data
    self._memory['flags'] = self._game.flag_data
    
    # Initialize the game's internal state
    self._game._init()

  def reset(self):
    """
    Reloads the current cart, effectively restarting the game.
    """
    self.load_game(self._cart)

  def step(self):
    """
    Performs one game update and draw cycle.
    """
    self._game._update()
    self._game._draw()

  def set_inputs(self, l=False, r=False, u=False, d=False, z=False, x=False):
    """
    Sets the button state based on boolean inputs.
    Optimized: Direct bit manipulation for setting button state.
    """
    state = 0
    if l: state |= (1 << K_LEFT)
    if r: state |= (1 << K_RIGHT)
    if u: state |= (1 << K_UP)
    if d: state |= (1 << K_DOWN)
    if z: state |= (1 << K_JUMP)
    if x: state |= (1 << K_DASH)
    self._btn_state = state

  def set_btn_state(self, state):
    """
    Sets the button state directly from an integer mask.
    """
    self._btn_state = state

  @property
  def game(self):
    return self._game

  # Removed input_display property as it's for debugging and not essential for gameplay
  # For debugging on RP2040, consider blinking LEDs or sending data over serial.

