print("Shipwrecked PCB Badge OS starting...")

from internal_os import internalos

badge = internalos.InternalOS.instance()

badge.start()