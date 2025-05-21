import machine
import utime

# Pin configuration (adjust to match your board)
BUSY = machine.Pin(27, machine.Pin.IN, machine.Pin.PULL_UP)   # Just pulled up, not used
RST  = machine.Pin(26, machine.Pin.OUT)
DC   = machine.Pin(25, machine.Pin.OUT)
CS   = machine.Pin(24, machine.Pin.OUT)

SCK  = machine.Pin(18)
MOSI = machine.Pin(19)
MISO = machine.Pin(20)  # Not used here

spi = machine.SPI(0, baudrate=10_000_000, polarity=0, phase=0, sck=SCK, mosi=MOSI, miso=MISO)

# -------------------------------------
# SPI Helpers
# -------------------------------------

def spi_write(byte_val):
    if isinstance(byte_val, int):
        spi.write(bytearray([byte_val]))
    else:
        spi.write(byte_val)

def write_cmd(cmd):
    CS.value(0)
    DC.value(0)  # Command mode
    spi_write(cmd)
    CS.value(1)

def write_data(data):
    CS.value(0)
    DC.value(1)  # Data mode
    spi_write(data)
    CS.value(1)

# -------------------------------------
# Fake busy wait (no real screen)
# -------------------------------------
def wait_fake_busy():
    print("Fake BUSY wait... (sleeping 50ms)")
    utime.sleep_ms(50)

# -------------------------------------
# Power up booster only
# -------------------------------------
def booster_test():
    print("Resetting panel...")
    RST.value(0)
    utime.sleep_ms(10)
    RST.value(1)
    utime.sleep_ms(10)

    print("Sending soft-start command (0x06)...")
    write_cmd(0x06)
    write_data(0x17)  # Typical SSD1681 soft-start params
    write_data(0x17)
    write_data(0x17)

    print("Sending power setting (0x01)...")
    write_cmd(0x01)
    write_data(0x03)  # VDS_EN, VDG_EN
    write_data(0x00)  # VCOM_HV ~ -2.5V
    write_data(0x2B)  # VGH = 15V
    write_data(0x2B)  # VGL = -15V

    print("Sending power ON (0x04)...")
    write_cmd(0x04)
    wait_fake_busy()

    print("Booster should now be active.")
    print("Measure PREVGH, PREVGL, and GDR pins.")

# -------------------------------------
# Main
# -------------------------------------
booster_test()

while True:
    print("Looping every 5s... Check voltages.")
    utime.sleep(5)
