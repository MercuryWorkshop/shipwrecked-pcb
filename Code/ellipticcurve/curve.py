#
# Elliptic Curve Equation
#
# y^2 = x^3 + A*x + B (mod P)
#
from .math import Math
from .point import Point


class CurveFp:

    def __init__(self, A, B, P, N, Gx, Gy, name, oid, nistName=None):
        self.A = A
        self.B = B
        self.P = P
        self.N = N
        self.G = Point(Gx, Gy)
        self.name = name
        self.nistName = nistName
        self.oid = oid  # ASN.1 Object Identifier

    def contains(self, p):
        """
        Verify if the point `p` is on the curve

        :param p: Point p = Point(x, y)
        :return: boolean
        """
        if not 0 <= p.x <= self.P - 1:
            return False
        if not 0 <= p.y <= self.P - 1:
            return False
        if (p.y**2 - (p.x**3 + self.A * p.x + self.B)) % self.P != 0:
            return False
        return True

    def length(self):
        return (1 + len("%x" % self.N)) // 2

    def y(self, x, isEven):
        ySquared = (pow(x, 3, self.P) + self.A * x + self.B) % self.P
        y = Math.modularSquareRoot(ySquared, self.P)
        if isEven != (y % 2 == 0):
            y = self.P - y
        return y


_curvesByOid = {tuple(curve.oid): curve for curve in []}


def add(curve):
    _curvesByOid[tuple(curve.oid)] = curve


def getByOid(oid):
    if oid not in _curvesByOid:
        raise Exception("Unknown curve with oid {oid}; The following are registered: {names}".format(
            oid=".".join([str(number) for number in oid]),
            names=", ".join([curve.name for curve in _curvesByOid.values()]),
        ))
    return _curvesByOid[oid]

import gc
print(f"Free memory before curve creation: {gc.mem_free()} bytes")
secp256k1 = CurveFp(
    name="secp256k1",
    A=0x0000000000000000000000000000000000000000000000000000000000000000,
    B=0x0000000000000000000000000000000000000000000000000000000000000007,
    P=0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f,
    N=0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141,
    Gx=0x79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798,
    Gy=0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8,
    oid=[1, 3, 132, 0, 10]
)
print(f"Free memory after curve creation: {gc.mem_free()} bytes")
add(secp256k1)
