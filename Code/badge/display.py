try:
    from typing import Union
except ImportError:
    # we're on an MCU, typing is not available
    pass

import framebuf
from microfont import MicroFont
import _thread

from internal_os.internalos import InternalOS

internal_os = InternalOS.instance()

width = 200
height = 200

def _is_display_allowed() -> bool:
    """
    Check if the display is allowed to be used.
    """
    return internal_os.apps.get_current_app_repr() == internal_os.apps.selected_fg_app

def sleep():
    """
    Put the display to sleep to save power.
    User code rarely has to call this, it's handled internally most of the time.
    """
    if not _is_display_allowed():
        raise RuntimeError("Cannot call display functions from a backgrounded app context.")
    internal_os.display.sleep_disp()

def show() -> None:
    """
    Push the contents of the internal framebuffer to the display.
    This does a full refresh of the E-Ink (takes a few seconds).
    NOTE: YOUR DRAWING WILL NOT DO ANYTHING UNTIL YOU CALL THIS FUNCTION!
    """
    if not _is_display_allowed():
        raise RuntimeError("Cannot call display functions from a backgrounded app context.")
    internal_os.display.show()

def fill(color: int) -> None:
    """
    Fill the entire display with a color.
    :param color: Color to fill (0=black, 1=white).
    """
    if not _is_display_allowed():
        raise RuntimeError("Cannot call display functions from a backgrounded app context.")
    internal_os.display.fill(color)

def pixel(x: int, y: int, color: int) -> None:
    """
    Set a pixel color.
    :param x: X coordinate of the pixel.
    :param y: Y coordinate of the pixel.
    :param color: Color of the pixel (0=black, 1=white).
    """
    if not _is_display_allowed():
        raise RuntimeError("Cannot call display functions from a backgrounded app context.")
    internal_os.display.pixel(x, y, color)

def hline(x: int, y: int, w: int, color: int) -> None:
    """
    Draw a horizontal line.
    :param x: X coordinate of the start of the line.
    :param y: Y coordinate of the line.
    :param w: Width of the line.
    :param color: Color of the line (0=black, 1=white).
    """
    if not _is_display_allowed():
        raise RuntimeError("Cannot call display functions from a backgrounded app context.")
    internal_os.display.hline(x, y, w, color)

def vline(x: int, y: int, h: int, color: int) -> None:
    """
    Draw a vertical line.
    :param x: X coordinate of the line.
    :param y: Y coordinate of the start of the line.
    :param h: Height of the line.
    :param color: Color of the line (0=black, 1=white).
    """
    if not _is_display_allowed():
        raise RuntimeError("Cannot call display functions from a backgrounded app context.")
    internal_os.display.vline(x, y, h, color)

def line(x1: int, y1: int, x2: int, y2: int, color: int) -> None:
    """
    Draw a line.
    :param x1: X coordinate of the start of the line.
    :param y1: Y coordinate of the start of the line.
    :param x2: X coordinate of the end of the line.
    :param y2: Y coordinate of the end of the line.
    :param color: Color of the line (0=black, 1=white).
    """
    if not _is_display_allowed():
        raise RuntimeError("Cannot call display functions from a backgrounded app context.")
    internal_os.display.line(x1, y1, x2, y2, color)

def rect(x: int, y: int, w: int, h: int, color: int) -> None:
    """
    Draw a rectangle (stroke only).
    :param x: X coordinate of the top-left corner.
    :param y: Y coordinate of the top-left corner.
    :param w: Width of the rectangle.
    :param h: Height of the rectangle.
    :param color: Color of the rectangle (0=black, 1=white).
    """
    if not _is_display_allowed():
        raise RuntimeError("Cannot call display functions from a backgrounded app context.")
    internal_os.display.rect(x, y, w, h, color)

def fill_rect(x: int, y: int, w: int, h: int, color: int) -> None:
    """
    Draw a filled rectangle.
    :param x: X coordinate of the top-left corner.
    :param y: Y coordinate of the top-left corner.
    :param w: Width of the rectangle.
    :param h: Height of the rectangle.
    :param color: Color of the rectangle (0=black, 1=white).
    """
    if not _is_display_allowed():
        raise RuntimeError("Cannot call display functions from a backgrounded app context.")
    internal_os.display.fill_rect(x, y, w, h, color)

def text(text: str, x: int, y: int, color: int = 0) -> None:
    """
    Draw 8x8 text on the display.
    :param text: The text to draw.
    :param x: X coordinate of the text.
    :param y: Y coordinate of the text.
    :param color: Color of the text (0=black, 1=white).
    """
    if not _is_display_allowed():
        raise RuntimeError("Cannot call display functions from a backgrounded app context.")
    internal_os.display.text(text, x, y, color)

import gc
print(f"Mem before fonts: {gc.mem_free()}")

nice_fonts = {
    18: MicroFont("fonts/victor_B_18.mfnt"),
    24: MicroFont("fonts/victor_B_24.mfnt"),
    32: MicroFont("fonts/victor_B_32.mfnt"),
    42: MicroFont("fonts/victor_B_42.mfnt"),
    54: MicroFont("fonts/victor_B_54.mfnt"),
    68: MicroFont("fonts/victor_B_68.mfnt"),
}

print(f"Mem after fonts: {gc.mem_free()}")

def nice_text(text: str, x: int, y: int, font: Union[int, MicroFont] = 18, color: int = 0, *, rot: int = 0, x_spacing: int = 0, y_spacing: int = 0) -> None:
    """
    Draw text using a nice font.
    Included fonts are Victor Mono Bold in 18, 24, 32, 42, 54, and 68 point sizes.
    If these are not adequate, you can provide a MicroFont instance with your own font.
    :param text: The text to draw.
    :param x: X coordinate of the text.
    :param y: Y coordinate of the text.
    :param font: Font size or a MicroFont instance. Default is 18.
    :param color: Color of the text (0=black, 1=white).
    :param rot: Rotation angle in degrees.
    :param x_spacing: Horizontal spacing between characters.
    :param y_spacing: Vertical spacing between lines.
    """
    if not _is_display_allowed():
        raise RuntimeError("Cannot call display functions from a backgrounded app context.")
    
    if isinstance(font, int):
        font = nice_fonts.get(font)
    if not font:
        raise ValueError(f"Invalid font size. Available built-in sizes: {', '.join(map(str, nice_fonts.keys()))}, or provide a MicroFont instance with your own font.")

    font.write(text, internal_os.display.display.framebuf, framebuf.MONO_HLSB, width, height, x, y, color, rot=rot, x_spacing=x_spacing, y_spacing=y_spacing)

    

def blit(fb: framebuf.FrameBuffer, x: int, y: int) -> None:
    """
    Blit a FrameBuffer onto the display.
    :param fb: The FrameBuffer to blit.
    :param x: X coordinate to start blitting.
    :param y: Y coordinate to start blitting.
    """
    if not _is_display_allowed():
        raise RuntimeError("Cannot call display functions from a backgrounded app context.")
    internal_os.display.blit(fb, x, y)

def import_pbm(file_path: str) -> framebuf.FrameBuffer:
    """
    Import a PBM image file (type P4) and return it as a FrameBuffer.
    :param file_path: Path to the PBM file.
    :return: FrameBuffer object containing the image.
    this converter is known to work: https://convertio.co/png-pbm/
    """
    with open(file_path, 'rb') as f:
        # Read the header
        header = f.readline().strip()
        if header != b'P4':
            raise ValueError("File is not a valid binary PBM file.")
        # Read the width and height
        dimensions = f.readline().strip()
        width, height = map(int, dimensions.split())
        # Read the pixel data
        pixel_data = bytearray(~b & 0xFF for b in f.read()) # the e-ink means the PBM format swaps black and white
        if len(pixel_data) != (width * height + 7) // 8:
            raise ValueError("Pixel data does not match specified dimensions.")
        # Create a FrameBuffer from the pixel data
        fb = framebuf.FrameBuffer(pixel_data, width, height, framebuf.MONO_HLSB)
    return fb
    