import logging

class PICO8():
  def __init__(self, cart):
    self._btn_state = 0
    self.load_game(cart)

  # game functions

  def btn(self, i):
    return self._btn_state & (2 ** i) != 0

  def mset(self, x, y, tile):
    self._memory['map'][x + y * 128] = tile

  def mget(self, x, y):
    return self._memory['map'][x + y * 128]

  def fget(self, n, f=None):
    flags = self._memory['flags'][n]
    return flags if f == None else flags & 2 ** f != 0

  # console commands

  # load game from cart
  def load_game(self, cart):
    logging.info(f"celeste classic: p8 load_game");
    self._cart = cart
    self._game = self._cart(self)
    logging.info(f"celeste classic: p8 _cart");
    self._memory = {
      'map': self._game.map_data,
      'flags': self._game.flag_data,
    }
    logging.info(f"celeste classic: p8 _flags");
    self._game._init()
    logging.info(f"celeste classic: p8 _init");

  # reload the current cart
  def reset(self):
    self.load_game(self._cart)

  # perform a game step
  def step(self):
    self._game._update()
    self._game._draw()

  # set button state from inputs
  def set_inputs(self, l=False, r=False, u=False, d=False, z=False, x=False):
    self.set_btn_state(l * 1 + r * 2 + u * 4 + d * 8 + z * 16 + x * 32)

  # set button state directly (0bxzdurl)
  def set_btn_state(self, state):
    self._btn_state = state

  @property
  def game(self):
    return self._game

  @property
  def input_display(self):
    l, r, u, d, z, x = ('▓▓' if self.btn(i) else '░░' for i in range(6))
    return f"        {u}\n{z}{x}  {l}{d}{r}"
