import belay
import time
from ellipticcurve import PrivateKey, Ecdsa
import struct
import serial
import sys

# ANNOUNCEMENT FORMAT:
# 1 byte: reserved (should be 0)
# 32 bytes: r-value of the ECDSA signature of the rest of the message
# 32 bytes: s-value of the ECDSA signature
# 4 bytes: announcement creation time (Unix timestamp, also serves as announcement ID)
# 1 byte: length of the message, in bytes
# 179 bytes: message text, padded with null bytes
MSG_FMT = "!B32s32sIB179s"
SIGLESS_MSG_FMT = "!IB179s"
try:
    with open("signing_key.txt", "r") as f:
        sk = PrivateKey.fromString(f.read())
except FileNotFoundError:
    print("No signing_key.txt file found. Grab it from Slack.")
    sys.exit(1)


message = input("Enter announcement message (max 179 characters): ")[:179]
message_bytes = message.encode("utf-8")
message_bytes = message_bytes.ljust(179, b"\0")
timestamp = int(time.time())

sigless_msg = struct.pack(SIGLESS_MSG_FMT, timestamp, len(message), message_bytes)
signature = Ecdsa.sign(sigless_msg, sk)
full_msg = struct.pack(MSG_FMT, 0, signature.r.to_bytes(32, byteorder="big"), signature.s.to_bytes(32, byteorder="big"), timestamp, len(message), message_bytes)
print(f"Full message length: {len(full_msg)} bytes")
print(f"Full message: {full_msg}")
# verify the signature
vk = sk.publicKey()
is_valid = Ecdsa.verify(sigless_msg, signature, vk)
print(f"Signature valid: {is_valid}")
print(f"Signature: r={signature.r.to_bytes(32, byteorder="big").hex()}, s={signature.s.to_bytes(32, byteorder="big").hex()}")

available_ports = serial.tools.list_ports.comports()
print("Available serial ports:")
for i, port in enumerate(available_ports):
    print(f"{i}: {port.device} - {port.description}")
port_index = int(input("Select the index of the serial port to use: "))
selected_port = available_ports[port_index].device

device = belay.Device(selected_port)

@device.setup
def setup():
    print("Shipwrecked PCB Badge OS starting...")
    from internal_os import internalos
    import time
    import asyncio
    badge = internalos.InternalOS.instance()
    badge.setup()

@device.task
def send_announcement(msg):
    
    # async def send_thing():
    #     print("waiting to send...")
    #     await asyncio.sleep(10)
    #     print(f"HEY! sending thing: {msg}")
    #     with open("/data/messenger/message_to_send.bin", "wb") as f:
    #         f.write(msg)
        
    #     await badge.apps.launch_app(badge.apps.get_app_by_path("/apps/messenger"))
    # asyncio.create_task(send_thing())
    # badge.run_forever()
    for i in range(3):
        print(f"Sending announcement, attempt {i+1}/3...")
        badge.radio._send_msg(b'\xff\xff', b'\x00\x03', msg)
        time.sleep(10)

setup()

print("Your announcement:")
print(full_msg)
confirm = input(f"Are you sure you want to send it? (y/n): ")
if not confirm.lower().startswith("y"):
    print("Aborting.")
    sys.exit(0)

# print(f"Sending announcement via {selected_port}...")
# for i in range(4):
#     print(f"Sending announcement, attempt {i+1}/5...")
#     try:
#         send_announcement(full_msg)
#     except Exception as e:
#         print(f"There was an error on this attempt. It's probably fine tho :p {e}")
#     time.sleep(3)
# last one
print("Sending announcement...")
send_announcement(full_msg)
print("Announcement sent.")