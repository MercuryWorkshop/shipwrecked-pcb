from .point import Point
from .curve import secp256k1
from .utils.binary import intFromHex


class PublicKey:

    def __init__(self, point, curve):
        self.point = point
        self.curve = curve

    @classmethod
    def fromCompressed(cls, string, curve=secp256k1):
        parityTag, xHex = string[:2], string[2:]
        if parityTag not in [_evenTag, _oddTag]:
            raise Exception("Compressed string should start with 02 or 03")
        x = intFromHex(xHex)
        y = curve.y(x, isEven=parityTag == _evenTag)
        return cls(point=Point(x, y), curve=curve)


_evenTag = "02"
_oddTag = "03"