import badge
import random

class App(badge.BaseApp):
    def on_open(self):
        self.result = None
        self._was_down = False
        badge.display.fill(1)
        badge.display.nice_text("Coin flip", 50, 0, font=badge.display.nice_fonts[24])
        badge.display.nice_text("Press any button to flip", 3, 100, font=badge.display.nice_fonts[18])
        badge.display.show()

    def justdrawit(self, cx: int, cy: int, r: int, color: int) -> None:
        for dy in range(-r, r + 1):
            dx = int(((r * r) - (dy * dy)) ** 0.5)
            x0 = cx - dx
            w = dx * 2 + 1
            badge.display.hline(x0, cy + dy, w, color)

    def renderCoin(self, heads: bool) -> None:
        cx = badge.display.width // 2
        cy = badge.display.height // 2
        r_outer = 70
        ring = 5
        r_inner = r_outer - ring

        badge.display.fill(1)
        self.justdrawit(cx, cy, r_outer, 0)
        self.justdrawit(cx, cy, r_inner, 1)

        mark = "H" if heads else "T"
        f = badge.display.nice_fonts[68]
        tx = cx - (f.max_width // 2)
        ty = cy - (f.height // 2)
        badge.display.nice_text(mark, tx, ty, font=f, color=0)

        badge.display.nice_text("Heads" if heads else "Tails", 72, 170, font=badge.display.nice_fonts[24])
        badge.display.show()

    def loop(self):
        down = any(badge.input.get_button(btn) for btn in range(1, 16))
        if down and not self._was_down:
            heads = bool(random.getrandbits(1))
            self.result = "Heads" if heads else "Tails"
            self.renderCoin(heads)
        self._was_down = down