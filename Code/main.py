print("Shipwrecked PCB Badge CFW starting...")

from internal_os import internalos

badge = internalos.InternalOS.instance()

badge.start()
