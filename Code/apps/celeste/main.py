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
        """
        The main game loop, called repeatedly for each frame.
        Optimized to minimize operations and memory allocation per frame.
        """
        # Get button inputs from the badge. These are efficient hardware reads.
        l = badge.input.get_button(badge.input.Buttons.SW11)
        r = badge.input.get_button(badge.input.Buttons.SW12)
        u = badge.input.get_button(badge.input.Buttons.SW13)
        d = badge.input.get_button(badge.input.Buttons.SW14)
        z = badge.input.get_button(badge.input.Buttons.SW15)
        x = badge.input.get_button(badge.input.Buttons.SW16)

        # Set the inputs for the PICO-8 game engine and advance the game state.
        # The performance here largely depends on the complexity of Celeste's internal logic.
        self.p8.set_inputs(l, r, u, d, z, x)
        self.p8.step()

        # Clear the entire display with white (color 1).
        # This is a necessary step for full frame redraws on the display.
        badge.display.fill(1)

        # Fixed display parameters, calculated once per loop (or could be class attributes).
        # Keeping them local for clarity, their impact on performance is minimal.
        tile_display_size = 12
        offset_x = (200 - (16 * tile_display_size)) // 2
        offset_y = (200 - (16 * tile_display_size)) // 2

        # Get direct references to PICO8 and Celeste game instances.
        p8 = self.p8
        g = self.p8.game # 'g' refers to the Celeste game instance

        # --- 1. Draw base tiles (walls, ground, spikes) ---
        # Optimized drawing: Only draw black pixels for solid/spike tiles.
        # White background is implicitly handled by badge.display.fill(1) at the start of the loop.
        for row_idx in range(16):
            for col_idx in range(16):
                # Get the raw tile ID from the game's map memory.
                tile = p8.mget(g.room.x * 16 + col_idx, g.room.y * 16 + row_idx)
                
                # Check tile flags (solid block or foreground) or if it's a spike.
                # `p8.fget` is part of the game engine's logic.
                if p8.fget(tile, 0) or p8.fget(tile, 4) or tile in self.spike_tiles:
                    # Calculate pixel coordinates.
                    x_pixel = offset_x + (col_idx * tile_display_size)
                    y_pixel = offset_y + (row_idx * tile_display_size)
                    
                    # Draw a filled black square. This is an efficient drawing operation.
                    badge.display.fill_rect(x_pixel, y_pixel, tile_display_size, tile_display_size, 0)

        # --- 2. Draw objects on top of the tiles ---
        # Iterate through all active objects in the game.
        for o in g.objects:
            # Skip objects marked for destruction.
            if o is None:
                continue
            
            # Check if the object type has a defined text representation and is visible.
            if type(o) in self.object_text_repr and o.spr != 0:
                # Retrieve the text string from the pre-computed dictionary.
                obj_text = self.object_text_repr[type(o)]

                # Calculate object's tile position (rounded for display).
                ox_tile = round(o.x / 8)
                oy_tile = round(o.y / 8)

                # Only draw if the object is within the visible map area.
                if 0 <= ox_tile <= 15 and 0 <= oy_tile <= 15:
                    # Calculate pixel coordinates for the main object sprite.
                    obj_x_pixel = offset_x + (ox_tile * tile_display_size)
                    obj_y_pixel = offset_y + (oy_tile * tile_display_size)

                    # Draw the text representation. `badge.display.text` can be a bottleneck
                    # if font rendering is computationally heavy.
                    badge.display.text(obj_text, obj_x_pixel, obj_y_pixel, 0)

                    # Handle drawing additional text for multi-tile objects or visual effects.
                    # These specific checks maintain the visual fidelity of the original Celeste.
                    if type(o) == g.platform and ox_tile + 1 <= 15:
                        badge.display.text(obj_text, obj_x_pixel + tile_display_size, obj_y_pixel, 0)
                    elif type(o) == g.fly_fruit:
                        if ox_tile - 1 >= 0:
                            badge.display.text(' »', obj_x_pixel - tile_display_size, obj_y_pixel, 0)
                        if ox_tile + 1 <= 15:
                            badge.display.text('« ', obj_x_pixel + tile_display_size, obj_y_pixel, 0)
                    elif type(o) == g.fake_wall:
                        if ox_tile + 1 <= 15:
                            badge.display.text(obj_text, obj_x_pixel + tile_display_size, obj_y_pixel, 0)
                        if oy_tile + 1 <= 15:
                            badge.display.text(obj_text, obj_x_pixel, obj_y_pixel + tile_display_size, 0)
                        if ox_tile + 1 <= 15 and oy_tile + 1 <= 15:
                            badge.display.text(obj_text, obj_x_pixel + tile_display_size, obj_y_pixel + tile_display_size, 0)

        # Push the rendered frame to the actual display.
        # This is typically the most time-consuming step for many displays, especially e-ink.
        badge.display.show()
