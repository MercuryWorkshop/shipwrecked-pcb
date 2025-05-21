import machine, utime
GDR_TEST = machine.Pin(15, machine.Pin.OUT)   # choose any spare GPIO

while True:
    GDR_TEST.value(1)
    utime.sleep_us(10)   # ~50 kHz, 50% duty (10 µs high + 10 µs low)
    GDR_TEST.value(0)
    utime.sleep_us(10)
