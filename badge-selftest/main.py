# a self-test program for the badge
# tests:
# - display
# - buttons
# - buzzer
# - LED
# - radio

from machine import Pin, SPI, I2C, PWM, unique_id
import utime

spi = SPI(0, baudrate=1_000_000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(19), miso=Pin(20))

print("--- Starting self-test---")
print("---- Testing LED ----")

led = PWM(Pin(16))
led.freq(5000)

led.duty_u16(10_000)  # Turn on LED
utime.sleep(3)  # Wait for 1 second

print("---- Testing display ----")

from einkdriver import EPD
disp_cs = Pin(24, Pin.OUT)
disp_dc = Pin(25, Pin.OUT)
disp_rst = Pin(26, Pin.OUT)
disp_busy = Pin(27, Pin.IN)

print("Initializing E-Ink display...")
display = EPD(spi, disp_cs, disp_dc, disp_rst, disp_busy)
display.init()

print("Displaying base image...")
display.fill(1)  # Fill with white
display.text("badge self-test", 10, 10, 0)
display.text("Press any button on the badge", 10, 30, 0)
display.text(f"Badge ID: {unique_id().hex()[-4:]}", 10, 50, 0) 
display.display()
display.sleep()
utime.sleep(5)  # Allow time for display to update

print("---- Testing buttons ----")
ADDRESS: int = 0x20  # I2C address of PCA9555
INPUT_PORT_0: int = 0x00
INPUT_PORT_1: int = 0x01
CONFIG_PORT_0: int = 0x06
CONFIG_PORT_1: int = 0x07

i2c = I2C(0, scl=Pin(1), sda=Pin(0))

# initialize the PCA9555 I/O expander
i2c.writeto_mem(ADDRESS, CONFIG_PORT_0, bytearray([0xff])) # set the bottom 8 pins as inputs
i2c.writeto_mem(ADDRESS, CONFIG_PORT_1, bytearray([0xff])) # set the top 8 pins as inputs

button_pressed = None
print("Press a button on the badge to continue...")

while button_pressed is None:
    raw_data = i2c.readfrom_mem(ADDRESS, INPUT_PORT_0, 2)
    for i in range(16):
        # Check if the button is pressed (active low)
        if not (raw_data[i // 8] & (1 << (i % 8))):
            button_pressed = i
            print(f"Button {i} pressed!")
            break
    utime.sleep(0.1)  # Polling delay

display.text(f"Button {button_pressed} pressed!", 10, 70, 0)
display.display()
display.sleep()

print("---- Testing buzzer ----")
def tone(frequency, duration):
    buzzer.freq(frequency)
    buzzer.duty_u16(10_000)  # Set duty cycle to 100%
    utime.sleep(duration)
    buzzer.duty_u16(0)  # Turn off buzzer

buzzer = PWM(Pin(28))
# simple melody
tone(523, 0.5) # C5
utime.sleep(0.1)
tone(392, 0.25) # G4
utime.sleep(0.05)
tone(392, 0.25) # G4
utime.sleep(0.05)
tone(415, 0.5) # G#4
utime.sleep(0.7)
tone(493, 0.5) # B4
utime.sleep(0.1)
tone(523, 0.5) # C5

led.duty_u16(0)  # Turn off LED

print("--- Test completed ---")