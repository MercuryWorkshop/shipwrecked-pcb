from machine import Pin, SPI, I2C, PWM
from sx1262 import SX1262
import time

ADDRESS = 0x20
INPUT_PORT_0 = 0x00
INPUT_PORT_1 = 0x01
CONFIG_PORT_0 = 0x06
CONFIG_PORT_1 = 0x07

i2c = I2C(0, scl=Pin(1), sda=Pin(0))
i2c.writeto_mem(ADDRESS, CONFIG_PORT_0, b'\xFF')  
i2c.writeto_mem(ADDRESS, CONFIG_PORT_1, b'\xFF')  

led = PWM(Pin(16))
led.freq(5000)

def flash_led(duration=0.15):
    led.duty_u16(5000)
    time.sleep(duration)
    led.duty_u16(0)

sx = SX1262(
    spi_bus=0,
    clk=18, mosi=19, miso=20,
    cs=21, irq=17, rst=23, gpio=22
)

print("Initializing LoRa...")
sx.begin(
    freq=923, bw=500.0, sf=12, cr=8, syncWord=0x12,
    power=10, currentLimit=60.0, preambleLength=8,
    implicit=False, implicitLen=0xFF,
    crcOn=True, txIq=False, rxIq=False,
    tcxoVoltage=0, useRegulatorLDO=False,
    blocking=False
)

def lora_callback(events):
    if events & SX1262.RX_DONE:
        msg, status = sx.recv()
        if msg:
            print("Received:", msg)
            flash_led()

sx.setBlockingCallback(False, lora_callback) #goofy ahh callback

last_button_state = 0xFFFF
def check_button():
    global last_button_state
    try:
        raw = i2c.readfrom_mem(ADDRESS, INPUT_PORT_0, 2)
    except OSError as e:
        print("I2C error:", e)
        return None

    state = int.from_bytes(raw, 'little')
    changed = last_button_state ^ state
    last_button_state = state
    if changed:
        for i in range(16):
            if changed & (1 << i) and not (state & (1 << i)):
                return i
    return None


MSG = b'BUTTON_PRESS'

print("press button to send")

while True:
    btn = check_button()
    if btn == 10:
        print("sending msg...")
        sx.send(MSG)
        flash_led()
        time.sleep(0.5)  # debounce
    time.sleep(0.05)
