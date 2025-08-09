import badge
import gc
from apps.celeste.PICO8 import PICO8
from apps.celeste.Celeste import Celeste

class App(badge.BaseApp):
    def on_open(self) -> None:
        free = gc.mem_free();
        self.logger.info(f"celeste classic: mem_free {free}");
        free = gc.mem_free();
        gc.collect();
        self.logger.info(f"celeste classic: mem_free after {free}");
        self.p8 = PICO8(Celeste);
        free = gc.mem_free();
        self.logger.info(f"celeste classic: mem_free init {free}");

    def loop(self) -> None:
        # Get button inputs from the badge
        l = badge.input.get_button(badge.input.Buttons.SW11);
        r = badge.input.get_button(badge.input.Buttons.SW12);
        u = badge.input.get_button(badge.input.Buttons.SW13);
        d = badge.input.get_button(badge.input.Buttons.SW14);
        z = badge.input.get_button(badge.input.Buttons.SW15);
        x = badge.input.get_button(badge.input.Buttons.SW16);

        # Set the inputs for the PICO-8 game engine
        self.p8.set_inputs(l, r, u, d, z, x);
        # Advance the game state by one step (update and draw logic within Celeste)
        self.p8.step();

        # Clear the display with white (color 1) before drawing the new frame
        badge.display.fill(1)

        # Get the string representation of the current game map from the Celeste object
        # The __str__ method in Celeste.py generates a 16x16 grid of 2-character strings
        # representing game tiles, separated by newlines.
        game_map_str = str(self.p8.game)
        
        # Split the string into individual lines (rows of game tiles)
        # .strip() is used to remove any potential trailing empty line from the split
        lines = game_map_str.strip().split('\n')

        # Define the pixel dimensions for each individual character.
        # Assuming a basic monospace font where each character is 4 pixels wide and 8 pixels tall.
        # This will render the 16x16 map (which is 32 characters wide in the string)
        # as a 128x128 pixel image on the display, matching PICO-8's resolution.
        char_pixel_width = 4
        char_pixel_height = 8

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

