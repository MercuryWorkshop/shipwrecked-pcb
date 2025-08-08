import badge
import urandom

class App(badge.BaseApp):
    def on_open(self):
        self.result = None
        badge.display.fill(1) #white bg
        badge.display.nice_text("Coin flip", 100, size=32, center=True)
        badge.display.nice_text("Press any button to flip", 100, 80, size=42, center=True)
        badge.display.show()

        def loop(self):
            # check for any button press except for home
            for btn in range(1, 16):
                if badge.input.get_button(btn):
                    self.result = "Heads" if urandom.getrandbits(1) else "Tails"
                    badge.display.fill(1)
                    badge.display.nice_text(self.result, 100, 80, size=-54, center=True)
                    badge.display.nice_text("Press to flip again", 100, 150, size=18, center=True)
                    badge.display.show()
                    break
            badge.utime.sleep_ms(50)
            
