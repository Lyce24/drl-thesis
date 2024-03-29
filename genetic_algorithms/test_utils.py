from enum import IntEnum

class Facelet(IntEnum):
    """""
    The names of the facelet positions of the cube
                  |************|
                  |*U1**U2**U3*|
                  |************|
                  |*U4**U5**U6*|
                  |************|
                  |*U7**U8**U9*|
                  |************|
     |************|************|************|************|
     |*L1**L2**L3*|*F1**F2**F3*|*R1**R2**R3*|*B1**B2**B3*|
     |************|************|************|************|
     |*L4**L5**L6*|*F4**F5**F6*|*R4**R5**R6*|*B4**B5**B6*|
     |************|************|************|************|
     |*L7**L8**L9*|*F7**F8**F9*|*R7**R8**R9*|*B7**B8**B9*|
     |************|************|************|************|
                  |************|
                  |*D1**D2**D3*|
                  |************|
                  |*D4**D5**D6*|
                  |************|
                  |*D7**D8**D9*|
                  |************|
    A cube definition string "UBL..." means for example: In position U1 we have the U-color, in position U2 we have the
    B-color, in position U3 we have the L color etc. according to the order U1, U2, U3, U4, U5, U6, U7, U8, U9, R1, R2,
    R3, R4, R5, R6, R7, R8, R9, F1, F2, F3, F4, F5, F6, F7, F8, F9, D1, D2, D3, D4, D5, D6, D7, D8, D9, L1, L2, L3, L4,
    L5, L6, L7, L8, L9, B1, B2, B3, B4, B5, B6, B7, B8, B9 of the enum constants.
    """
    
    U1 = 0
    U2 = 1
    U3 = 2
    U4 = 3
    U5 = 4
    U6 = 5
    U7 = 6
    U8 = 7
    U9 = 8
    R1 = 9
    R2 = 10
    R3 = 11
    R4 = 12
    R5 = 13
    R6 = 14
    R7 = 15
    R8 = 16
    R9 = 17
    F1 = 18
    F2 = 19
    F3 = 20
    F4 = 21
    F5 = 22
    F6 = 23
    F7 = 24
    F8 = 25
    F9 = 26
    D1 = 27
    D2 = 28
    D3 = 29
    D4 = 30
    D5 = 31
    D6 = 32
    D7 = 33
    D8 = 34
    D9 = 35
    L1 = 36
    L2 = 37
    L3 = 38
    L4 = 39
    L5 = 40
    L6 = 41
    L7 = 42
    L8 = 43
    L9 = 44
    B1 = 45
    B2 = 46
    B3 = 47
    B4 = 48
    B5 = 49
    B6 = 50
    B7 = 51
    B8 = 52
    B9 = 53


class Color(IntEnum):
    """ The possible colors of the cube facelets. Color U refers to the color of the U(p)-face etc.
    Also used to name the faces itself."""
    U = 0
    D = 1
    L = 2
    R = 3
    B = 4
    F = 5


class Move(IntEnum):
    """The moves in the faceturn metric. Not to be confused with the names of the facelet positions in class Facelet."""
    U1 = 0 # U(p) face clockwise
    U3 = 1 # U(p) face counter-clockwise
    R1 = 2 # R(ight) face clockwise
    R3 = 3 # R(ight) face counter-clockwise
    F1 = 4 # F(ront) face clockwise
    F3 = 5 # F(ront) face counter-clockwise
    D1 = 6 # D(own) face clockwise
    D3 = 7 # D(own) face counter-clockwise
    L1 = 8 # L(eft) face clockwise
    L3 = 9 # L(eft) face counter-clockwise
    B1 = 10 # B(ack) face clockwise
    B3 = 11 # B(ack) face counter-clockwise

move_dict = {
    Move.U1: "U",
    Move.U3: "U'",
    Move.R1: "R",
    Move.R3: "R'",
    Move.F1: "F",
    Move.F3: "F'",
    Move.D1: "D",
    Move.D3: "D'",
    Move.L1: "L",
    Move.L3: "L'",
    Move.B1: "B",
    Move.B3: "B'",
}

color_dict = {
    0 : [1, 0, 0, 0, 0, 0],
    1 : [0, 1, 0, 0, 0, 0],
    2 : [0, 0, 1, 0, 0, 0],
    3 : [0, 0, 0, 1, 0, 0],
    4 : [0, 0, 0, 0, 1, 0],
    5 : [0, 0, 0, 0, 0, 1]
}