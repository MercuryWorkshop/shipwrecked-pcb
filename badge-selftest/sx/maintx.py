from sx1262 import SX1262
import time

# ─── RP2040 / Pico pin map you described ───────────────────────────────
# SCK   → GP18
# MOSI  → GP19
# MISO  → GP20
# CS    → GP21   (NSS)
# IRQ   → GP17   (DIO1)
# RST   → GP23
# BUSY  → GP22   (passed as gpio=22)

sx = SX1262(
    spi_bus=0,          # use SPI0 for pins 18/19/20
    clk=18,             # SCK  -> GP18
    mosi=19,            # MOSI -> GP19
    miso=20,            # MISO -> GP20
    cs=21,              # NSS  -> GP21
    irq=17,             # DIO1 -> GP17
    rst=23,             # RST  -> GP23
    gpio=22             # BUSY -> GP22  (library names it "gpio")
)

# ─── LoRa initialisation ────────────────────────────────────────────────
print(
sx.begin(
    freq=923,
    bw=500.0,
    sf=12,
    cr=8,
    syncWord=0x12,
    power=-5,
    currentLimit=60.0,
    preambleLength=8,
    implicit=False,
    implicitLen=0xFF,
    crcOn=True,
    txIq=False,
    rxIq=False,
    tcxoVoltage=0,
    useRegulatorLDO=False,
    blocking=True
))

""" while True:
    msg, err = sx.recv()
    if msg:
        print(msg)
        print(SX1262.STATUS[err])
 """
while True:
    sx.send(b'Hello World!')
    print('Hello World!')
    time.sleep(10)