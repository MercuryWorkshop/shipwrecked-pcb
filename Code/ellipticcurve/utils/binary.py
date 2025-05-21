from binascii import b2a_base64, a2b_base64
from .compatibility import safeHexFromBinary, safeBinaryFromHex, toString


def hexFromInt(number):
    hexadecimal = "{0:x}".format(number)
    if len(hexadecimal) % 2 == 1:
        hexadecimal = "0" + hexadecimal
    return hexadecimal


def intFromHex(hexadecimal):
    return int(hexadecimal, 16)


def hexFromByteString(byteString):
    return safeHexFromBinary(byteString)


def byteStringFromHex(hexadecimal):
    return safeBinaryFromHex(hexadecimal)


def numberFromByteString(byteString):
    return intFromHex(hexFromByteString(byteString))


def base64FromByteString(byteString):
    return toString(b2a_base64(byteString))


def byteStringFromBase64(base64String):
    return a2b_base64(base64String)


def bitsFromHex(hexadecimal):
    return format(intFromHex(hexadecimal), 'b').zfill(4 * len(hexadecimal))
