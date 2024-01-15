print("Ocreeb MK 2 Starting ...")

import board
import busio
import displayio

from kb import OcreebMK2
from kmk.keys import KC
from kmk.modules.layers import Layers
from kmk.modules.encoder import EncoderHandler
from kmk.extensions.media_keys import MediaKeys

from ocreeb.ocreeb_module import ocreebModule

# macropad settings
ocreeb_rgb = True
ocreeb_oled = True
ocreeb_modules = True
layers_names = ['Layer 1', 'Layer 2', 'Layer 3']

displayio.release_displays()
i2c = busio.I2C(scl=board.SCL, sda=board.SDA, frequency=400000)

layers = Layers()
encoder_handler = EncoderHandler()

# init external modules examples depending on the hardware on each one
half_combo = ocreebModule(i2c, addr=0x50, buttons=(10, 11, 12,), num_encoders=1, enc_buttons=(3,), rgb_pin=14, rgb_count=2, rgb_fill=0x008000)
half_faders = ocreebModule(i2c, addr=0x60, analog=(14, 15,), rgb_pin=0, rgb_count=2, rgb_fill=0x008000)
half_dials = ocreebModule(i2c, addr=0x70, num_encoders =4, enc_buttons =(5, 2, 16, 12), rgb_pin=0, rgb_count=2, rgb_fill=0x008000)
full_combo = ocreebModule(i2c, addr=0x52, buttons=(10, 11, 12, 13,), num_encoders=1, rgb_pin=14, rgb_count=4, rgb_fill=0x008000)

# config the main the macropad and pass the external modules
keyboard = OcreebMK2(i2c, layers_names, ocreeb_rgb, ocreeb_oled, ocreeb_modules)
keyboard.modules = [layers, encoder_handler, half_combo, half_dials, half_faders, full_combo]

# this is the encoder on the macropad. Needs to be moved to kb.py
encoder_handler.pins = ((board.D9, board.D10, board.D8,),)

keyboard.extensions.append(MediaKeys())
# keyboard.debug_enabled = True

# ---------------- Main macropad maps ---------------- 
keyboard.keymap = [
    [
        KC.NO,     KC.NO,      KC.NO,      KC.NO,
        KC.NO,     KC.NO,      KC.NO,      KC.NO,
        KC.NO,     KC.NO,      KC.NO,      KC.NO,
    ]   # Layer 1
]

encoder_handler.map = [ 
    (( KC.NO,     KC.NO,      KC.NO),), # Layer 1
    (( KC.NO,     KC.NO,      KC.NO),), # Layer 2
    (( KC.NO,     KC.NO,      KC.NO),), # Layer 3
    ]
# ----------------

# ---------------- Combo module example maps (1 switched encoder, 3 switches) ---------------- 
half_combo.key_map = [
    [ KC.NO,     KC.NO,      KC.NO, ] # Layer 1
]

half_combo.enc_map = [
    (( KC.NO,     KC.NO,      KC.NO),), # Layer 1
    (( KC.NO,     KC.NO,      KC.NO),), # Layer 2
    (( KC.NO,     KC.NO,      KC.NO),), # Layer 3
    ]
# ---------------- 

# ---------------- Dials module example maps (4 switched encoders) ---------------- 
half_dials.enc_map = [
    (( KC.NO,  KC.NO,  KC.NO),   ( KC.NO,  KC.NO,  KC.NO),    ( KC.NO,  KC.NO,  KC.NO),    ( KC.NO,  KC.NO,  KC.NO), ), # Layer 1
    (( KC.NO,  KC.NO,  KC.NO),   ( KC.NO,  KC.NO,  KC.NO),    ( KC.NO,  KC.NO,  KC.NO),    ( KC.NO,  KC.NO,  KC.NO), ), # Layer 2
    (( KC.NO,  KC.NO,  KC.NO),   ( KC.NO,  KC.NO,  KC.NO),    ( KC.NO,  KC.NO,  KC.NO),    ( KC.NO,  KC.NO,  KC.NO), ), # Layer 3
    ]
# ---------------- 

# ---------------- Faders module - example midi notes (2 slider pots) ---------------- 
half_faders.analog_map = [ 40, 60 ]
# ---------------- 

# ---------------- Combo module maps (1 encoder, 4 switches) ---------------- 
full_combo.key_map = [
    [ KC.NO,     KC.NO,     KC.NO,     KC.NO, ] # Layer 1
]

full_combo.enc_map = [
    (( KC.NO,     KC.NO,      KC.NO),), # Layer 1
    (( KC.NO,     KC.NO,      KC.NO),), # Layer 2
    (( KC.NO,     KC.NO,      KC.NO),), # Layer 3
    ]
# ----------------

if __name__ == '__main__':
    keyboard.go()