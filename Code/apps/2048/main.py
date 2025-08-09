import badge
import random

import copy
try:
    from typing import Tuple, List
except ImportError:
    # we're on an MCU, typing is not available
    pass

class App(badge.BaseApp):
    def on_open(self):
        self.game = Game2048()
        self.renderer = BadgeRenderer()
        self.u_was_down = False
        self.d_was_down = False
        self.l_was_down = False
        self.r_was_down = False

    def loop(self):
        # down = any(badge.input.get_button(btn) for btn in range(1, 16))
        # if down and not self._was_down:
        #     heads = bool(random.getrandbits(1))
        #     self.result = "Heads" if heads else "Tails"
        #     self.renderCoin(heads)
        # self._was_down = down
        up = badge.input.get_button(badge.input.Buttons.SW10)
        down = badge.input.get_button(badge.input.Buttons.SW17)
        left = badge.input.get_button(badge.input.Buttons.SW11)
        right = badge.input.get_button(badge.input.Buttons.SW5)
        ok = badge.input.get_button(badge.input.Buttons.SW4)

        if up and not self.u_was_down:
            self.u_was_down = True
            moved = self.game.move("up")
            if moved:
                self.renderer.render(self.game.get_grid(), self.game.get_score())

        self.u_was_down = up

        if down and not self.d_was_down:
            self.d_was_down = True
            moved = self.game.move("down")
            if moved:
                self.renderer.render(self.game.get_grid(), self.game.get_score())
        self.d_was_down = down

        if left and not self.l_was_down:
            self.l_was_down = True
            moved = self.game.move("left")
            if moved:
                self.renderer.render(self.game.get_grid(), self.game.get_score())
        self.l_was_down = left

        if right and not self.r_was_down:
            self.r_was_down = True
            moved = self.game.move("right")
            if moved:
                self.renderer.render(self.game.get_grid(), self.game.get_score())
        self.r_was_down = right

        if ok:
            # Reset the game if OK is pressed
            self.game.reset()
            self.renderer.render(self.game.get_grid(), self.game.get_score())
            badge.buzzer.tone(440, 0.1)


class Game2048:
    """
    A minimal but fully functional 2048 game engine.

    Parameters
    ----------
    size : int, optional
        The dimension of the board (default is 4 for a 4x4 board).
    seed : int | None, optional
        Optional random seed for reproducibility. If None, system RNG is used.
    """

    def __init__(self, size: int = 4, seed: int | None = None) -> None:
        self.size = size
        self.grid: List[List[int]] = [[0] * size for _ in range(size)]
        self.score: int = 0
        if seed is not None:
            random.seed(seed)
        self.reset()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Reset the board to a new game state."""
        self.grid = [[0] * self.size for _ in range(self.size)]
        self.score = 0
        # Place two initial tiles
        self.add_random_tile()
        self.add_random_tile()

    def move(self, direction: str) -> bool:
        """
        Execute a move.

        Parameters
        ----------
        direction : str
            One of 'up', 'down', 'left', or 'right'.

        Returns
        -------
        bool
            True if the board changed; False otherwise.
        """
        dir_map = {
            "up": self._move_up,
            "down": self._move_down,
            "left": self._move_left,
            "right": self._move_right,
        }
        if direction not in dir_map:
            raise ValueError(f"Invalid move direction: {direction}")

        moved, score_gain = dir_map[direction]()
        if moved:
            self.score += score_gain
            self.add_random_tile()
        return moved

    def is_game_over(self) -> bool:
        """
        Return True if no moves are possible.

        The method tests each direction without altering the board state.
        """
        dir_map = {
            "up": self._move_up,
            "down": self._move_down,
            "left": self._move_left,
            "right": self._move_right,
        }
        for d in dir_map:
            snapshot_grid = copy.deepcopy(self.grid)
            snapshot_score = self.score
            moved, _ = dir_map[d]()
            if moved:  # a move is possible; revert and return False
                self.grid = snapshot_grid
                self.score = snapshot_score
                return False
        return True

    def get_grid(self) -> List[List[int]]:
        """Return a deep copy of the board."""
        return copy.deepcopy(self.grid)

    def get_score(self) -> int:
        """Return the current score."""
        return self.score

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def add_random_tile(self) -> None:
        """Add a new tile (2 or 4) to a random empty cell."""
        empties = [(r, c)
                   for r in range(self.size)
                   for c in range(self.size)
                   if self.grid[r][c] == 0]
        if not empties:
            return
        r, c = random.choice(empties)
        # Standard 90% 2 / 10% 4 distribution
        self.grid[r][c] = 4 if random.random() < 0.1 else 2

    def _move_left(self) -> Tuple[bool, int]:
        """Move all tiles to the left."""
        moved = False
        score_gain = 0
        for r in range(self.size):
            row = self.grid[r]
            new_row, gained, changed = self._compress_and_merge(row)
            if changed:
                moved = True
            self.grid[r] = new_row
            score_gain += gained
        return moved, score_gain

    def _move_right(self) -> Tuple[bool, int]:
        """Move all tiles to the right."""
        moved = False
        score_gain = 0
        for r in range(self.size):
            row = list(reversed(self.grid[r]))
            new_row, gained, changed = self._compress_and_merge(row)
            if changed:
                moved = True
            self.grid[r] = list(reversed(new_row))
            score_gain += gained
        return moved, score_gain

    def _move_up(self) -> Tuple[bool, int]:
        """Move all tiles up."""
        moved = False
        score_gain = 0
        for c in range(self.size):
            col = [self.grid[r][c] for r in range(self.size)]
            new_col, gained, changed = self._compress_and_merge(col)
            if changed:
                moved = True
            for r in range(self.size):
                self.grid[r][c] = new_col[r]
            score_gain += gained
        return moved, score_gain

    def _move_down(self) -> Tuple[bool, int]:
        """Move all tiles down."""
        moved = False
        score_gain = 0
        for c in range(self.size):
            # Read column from bottom to top
            col = [self.grid[r][c] for r in reversed(range(self.size))]
            new_col, gained, changed = self._compress_and_merge(col)
            if changed:
                moved = True
            # Place back reversed: index 0 of new_col goes to bottom row
            for idx, val in enumerate(new_col):
                self.grid[self.size - 1 - idx][c] = val
            score_gain += gained
        return moved, score_gain

    def _compress_and_merge(
        self,
        line: List[int],
    ) -> Tuple[List[int], int, bool]:
        """
        Compress a single row/column and merge tiles.

        Returns:
            new_line (list): the processed line with zeros padded at the end
            gained_score (int): sum of merged tile values
            changed (bool): whether the line was altered
        """
        nonzeros = [x for x in line if x != 0]
        new_line: List[int] = []
        i = 0
        score_gain = 0
        while i < len(nonzeros):
            if i + 1 < len(nonzeros) and nonzeros[i] == nonzeros[i + 1]:
                merged_value = nonzeros[i] * 2
                new_line.append(merged_value)
                score_gain += merged_value
                i += 2  # skip the next one
            else:
                new_line.append(nonzeros[i])
                i += 1
        # Pad zeros to fill the line
        new_line.extend([0] * (self.size - len(new_line)))
        changed = new_line != line
        return new_line, score_gain, changed

    def _undo_move(self, direction: str) -> None:
        """No longer needed; kept for backward compatibility."""
        pass


# ----------------------------------------------------------------------
# Rendering interface
# ----------------------------------------------------------------------
class Renderer:
    """Abstract renderer that knows how to display the board."""

    def render(self, grid: List[List[int]], score: int) -> None:
        """
        Render the given grid and score.
        Subclasses must implement this method.
        """
        raise NotImplementedError("Renderer subclasses must implement 'render'.")



class BadgeRenderer(Renderer):
    """Renderer for the 2048 game using the badge display."""

    def render(self, grid: List[List[int]], score: int) -> None:
        """
        Render the given grid and score on the badge display.
        """
        badge.display.fill(1)  # Clear the display
        cell_size = 32  # Size of each cell in pixels
        for r in range(len(grid)):
            for c in range(len(grid[r])):
                value = grid[r][c]
                if value > 0:
                    # Draw the cell with its value
                    x = c * cell_size
                    y = r * cell_size
                    badge.display.rect(x, y, cell_size, cell_size, 0)  # Draw border
                    badge.display.nice_text(str(value), x + 4, y + 4, font=24, color=0)
        # Display the score at the top
        badge.display.nice_text(f"Score: {score}", 0, 0, font=18, color=0)
        badge.display.show()


# class TerminalRenderer(Renderer):
#     """A simple terminal renderer using ASCII characters."""

#     def __init__(self, width: int = 4) -> None:
#         self.width = width
#         # Initial guess for cell width; will be overridden in render if needed.
#         self.cell_width = len(str(2 ** width))

#     def render(self, grid: List[List[int]], score: int) -> None:
#         os.system("cls" if os.name == "nt" else "clear")
#         print(f"Score: {score}\n")

#         size = len(grid[0]) if grid else 0
#         # Determine a suitable cell width based on the largest number currently present.
#         max_val = max(max(row) for row in grid) if grid else 0
#         cell_width = len(str(max_val)) if max_val > 0 else self.cell_width

#         horizontal_line = "+" + ("-" * (cell_width + 2)) * size + "+"

#         for row in grid:
#             line = "|"
#             for val in row:
#                 cell = f"{val}".center(cell_width)
#                 line += f" {cell} |"
#             print(line)
#             print(horizontal_line)
