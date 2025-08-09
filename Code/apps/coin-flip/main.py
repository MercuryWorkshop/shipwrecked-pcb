import badge
import random

class App(badge.BaseApp):
    def on_open(self):
        self.result = None
        badge.display.fill(1) #white bg
        badge.display.nice_text("Coin flip", 0, 0, font=badge.display.nice_fonts[24])
        badge.display.nice_text("Press any button to flip", 0, 100, font=badge.display.nice_fonts[24])
        badge.display.show()

    def loop(self):
        # check for any button press except for home
        for btn in range(1, 16):
            if badge.input.get_button(btn):
                self.result = "Heads" if random.getrandbits(1) else "Tails"
                badge.display.fill(1)
                badge.display.nice_text(self.result, 0, 0, font=badge.display.nice_fonts[24])
                badge.display.nice_text("Press to flip again", 0, 100, font=badge.display.nice_fonts[16])
                badge.display.show()
                break
        
