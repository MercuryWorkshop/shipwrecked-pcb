import badge
import gc
from apps.celeste.PICO8 import PICO8
from apps.celeste.Celeste import Celeste

class App(badge.BaseApp):
    def on_open(self) -> None:
        """
        Initializes the game and pre-computes drawing assets.
        This method is called once when the application starts,
        reducing repeated allocations in the main loop.
        """
        free = gc.mem_free()
        self.logger.info(f"celeste classic: mem_free {free}")
        gc.collect() # Force garbage collection to free up initial memory
        free = gc.mem_free()
        self.logger.info(f"celeste classic: mem_free after {free}")
        
        self.p8 = PICO8(Celeste) # Initialize the PICO-8 game engine with Celeste
        free = gc.mem_free()
        self.logger.info(f"celeste classic: mem_free init {free}")

        # --- Performance Optimization: Pre-compute unchanging data ---
        # Define text representations for various game objects once.
        # This dictionary is accessed frequently in the loop, so creating it here
        # prevents repeated memory allocations and dictionary construction.
        self.object_text_repr = {
            self.p8.game.spring: 'ΞΞ',
            self.p8.game.fall_floor: '▒▒',
            self.p8.game.balloon: '()',
            self.p8.game.key: '¤¬',
            self.p8.game.chest: '╔╗',
            self.p8.game.fruit: '{}',
            self.p8.game.fly_fruit: '{}',
            self.p8.game.fake_wall: '▓▓',
            self.p8.game.platform: 'oo',
            self.p8.game.player: ':D',
            self.p8.game.player_spawn: ':D'
        }
        # Define the set of spike tile IDs once.
        # Using a set provides efficient lookup (O(1) on average).
        self.spike_tiles = {17, 27, 43, 59}

    def loop(self) -> None:
        # Get button inputs from the badge
        l = badge.input.get_button(badge.input.Buttons.SW12);
        r = badge.input.get_button(badge.input.Buttons.SW11);
        u = badge.input.get_button(badge.input.Buttons.SW13);
        d = badge.input.get_button(badge.input.Buttons.SW14);
        z = badge.input.get_button(badge.input.Buttons.SW15);
        x = badge.input.get_button(badge.input.Buttons.SW16);

        # Set the inputs for the PICO-8 game engine and advance the game state.
        # The performance here largely depends on the complexity of Celeste's internal logic.
        self.p8.set_inputs(l, r, u, d, z, x)
        self.p8.step()

        badge.utils.set_led_pwm(65535)
        # Clear the entire display with white (color 1).
        # This is a necessary step for full frame redraws on the display.
        badge.display.fill(1)

        # Get the string representation of the current game map from the Celeste object
        # The __str__ method in Celeste.py generates a 16x16 grid of 2-character strings
        # representing game tiles, separated by newlines.
        game_map_str = str(self.p8.game)

        # Split the string into individual lines (rows of game tiles)
        # .strip() is used to remove any potential trailing empty line from the split
        lines = game_map_str.strip().split('\n')

        # Get direct references to PICO8 and Celeste game instances.
        p8 = self.p8
        g = self.p8.game # 'g' refers to the Celeste game instance

        # Iterate through each row and column of the game map
        for row_idx, line in enumerate(lines):
            # Each 'line' in the game_map_str contains 16 game tiles.
            # Since each game tile is represented by 2 characters (e.g., '██', '  '),
            # the character length of each line is 16 * 2 = 32 characters.
            for tile_col_idx in range(16): # Iterate for 16 game tiles horizontally
                # Extract the 2-character string that represents the current game tile
                # For example, if tile_col_idx is 0, it gets chars 0-1; if 1, chars 2-3, etc.
                char_pair = line[tile_col_idx * 2 : (tile_col_idx + 1) * 2]

                # Calculate the pixel coordinates (x, y) for where to draw this game tile
                # Each game tile will occupy (2 * char_pixel_width) horizontally and char_pixel_height vertically
                x_pixel = tile_col_idx * (2 * char_pixel_width)
                y_pixel = row_idx * char_pixel_height

                # Draw the 2-character string (representing the game tile) on the display
                # color=0 for black text.
                badge.display.text(char_pair, x_pixel, y_pixel, color=0)

        # After all drawing commands, refresh the actual display
        badge.display.show();
