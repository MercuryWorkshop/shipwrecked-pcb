from binascii import hexlify, unhexlify

stringTypes = (str,)
intTypes = (int, float)

def toString(string, encoding="utf-8"):
    return string.decode(encoding)

def toBytes(string, encoding="utf-8"):
    return string.encode(encoding)

def safeBinaryFromHex(hexadecimal):
    if len(hexadecimal) % 2 == 1:
        hexadecimal = "0" + hexadecimal
    return unhexlify(hexadecimal)

def safeHexFromBinary(byteString):
    return toString(hexlify(byteString))