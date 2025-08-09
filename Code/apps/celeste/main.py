import badge
import gc
from apps.celeste.PICO8 import PICO8
from apps.celeste.Celeste import Celeste

class App(badge.BaseApp):
    def on_open(self) -> None:
        self.logger.info(f"celeste classic: mem_free {gc.mem_free()}");
        gc.collect()
        self.logger.info(f"celeste classic: mem_free after {gc.mem_free()}");
        self.p8 = PICO8(Celeste)
        self.logger.info(f"celeste classic: mem_free init {gc.mem_free()}");

    def loop(self) -> None:
        l = badge.input.get_button(badge.input.Buttons.SW11);
        r = badge.input.get_button(badge.input.Buttons.SW12);
        u = badge.input.get_button(badge.input.Buttons.SW13);
        d = badge.input.get_button(badge.input.Buttons.SW14);
        z = badge.input.get_button(badge.input.Buttons.SW15);
        x = badge.input.get_button(badge.input.Buttons.SW16);
        self.p8.set_inputs(l, r, u, d, z, x);
        self.p8.step();

        badge.display.fill(1)
        badge.display.nice_text(str(self.p8.game), 0, 0, font=badge.display.nice_fonts[24], color=0, rot=0, x_spacing=0, y_spacing=0);
