import badge
from PICO8 import PICO8
from Carts.Celeste import Celeste

class App(badge.BaseApp):
    p8 = PICO8(Celeste)

    def on_open(self) -> None:
        self.logger.info("celeste classic 1!!");

    def loop(self) -> None:
        l = badge.input.get_button(badge.input.Buttons.SW11);
        r = badge.input.get_button(badge.input.Buttons.SW12);
        u = badge.input.get_button(badge.input.Buttons.SW13);
        d = badge.input.get_button(badge.input.Buttons.SW14);
        z = badge.input.get_button(badge.input.Buttons.SW15);
        x = badge.input.get_button(badge.input.Buttons.SW16);
        p8.set_inputs(l, r, u, d, z, x);
        p8.step();

        badge.display.nice_text(str(p8.game), 0, 0, font=badge.display.nice_fonts[24], color=0, rot=0, x_spacing=0, y_spacing=0);
