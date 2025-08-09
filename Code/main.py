print("Shipwrecked PCB Badge CFW starting...")

from internal_os import internalos
from machine import unique_id
import json

global badge_id
badge_id = unique_id()
print(f"Original ID: {badge_id.hex()}")

with open("/config.json", 'r') as f:
    config = json.load(f)
    id = bytes(config.get('badgeId', 0xffff))
    if id != 0xffff:
        badge_id = id
        print(f"ID OVERRIDE: {badge_id.hex()}")


badge = internalos.InternalOS.instance()

badge.start()
