COLORS = {
    0:  {"Name": "Off", "Hex": '000000'},
    10: {"Name": "Blue", "Hex": '4a418a'},
    20: {"Name": "Candlelight", "Hex": 'ebb63e'},
    30: {"Name": "Cold sky", "Hex": 'dcf0f8'},
    40: {"Name": "Cool daylight", "Hex": 'eaf6fb'},
    50: {"Name": "Cool white", "Hex": 'f5faf6'},
    60: {"Name": "Dark Peach", "Hex": 'da5d41'},
    70: {"Name": "Light Blue", "Hex": '6c83ba'},
    80: {"Name": "Light Pink", "Hex": 'e8bedd'},
    90: {"Name": "Light Purple", "Hex": 'c984bb'},
    100: {"Name": "Lime", "Hex": 'a9d62b'},
    110: {"Name": "Peach", "Hex": 'e57345'},
    120: {"Name": "Pink", "Hex": 'e491af'},
    130: {"Name": "Saturated Red", "Hex": 'dc4b31'},
    140: {"Name": "Saturated Pink", "Hex": 'd9337c'},
    150: {"Name": "Saturated Purple", "Hex": '8f2686'},
    160: {"Name": "Sunrise", "Hex": 'f2eccf'},
    170: {"Name": "Yellow", "Hex": 'd6e44b'},
    180: {"Name": "Warm Amber", "Hex": 'e78834'},
    190: {"Name": "Warm glow", "Hex": 'efd275'},
    200: {"Name": "Warm white", "Hex": 'f1e0b5'}
}

WB = {
    0:  {"Name": "Off", "Hex": '000000'},
    10: {"Name": "Cold", "Hex": 'f5faf6'},
    20: {"Name": "Normal", "Hex": 'f1e0b5'},
    30: {"Name": "Warm", "Hex": 'efd275'}
}


TEST = { "a":"Test", "b":"Test"}

d = {'x': 1, 'y': 2, 'z': 3} 

def color(level):
    return COLORS[level]

def wb(level):
    return WB[level]

def colorLevelDefinitions():
    levels=""
    actions=""
    for key, aColor in sorted(COLORS.items()):
        levels="{0}{1}|".format(levels, aColor["Name"])
        actions="{0}{1}|".format(actions, "")

    return levels[:-1], actions[:-1]

def colorLevelForHex(hex):
    for key in COLORS:
        if COLORS[key]["Hex"] == hex:
            return key
            

def wbLevelForHex(hex):
    for key in WB:
        if WB[key]["Hex"] == hex:
            return key

def wbLevelDefinitions():
    levels=""
    actions=""
    for key, aColor in sorted(WB.items()):
        levels="{0}{1}|".format(levels, aColor["Name"])
        actions="{0}{1}|".format(actions, "")

    return levels[:-1], actions[:-1]
