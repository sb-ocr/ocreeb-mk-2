from kmk.modules import Module

import struct
import usb_midi
import adafruit_midi

from adafruit_seesaw import neopixel
from adafruit_seesaw.seesaw import Seesaw
from adafruit_simplemath import map_range
from adafruit_midi.control_change import ControlChange

from .ocreeb_encoders import OcreebEncoders
from .ocreeb_buttons import OcreebButtons
from .ocreeb_analog import OcreebAnalog

class ocreebModule(Module):
    def __init__(self, i2c, addr=0x49, buttons=(), num_encoders=0, enc_buttons=(), analog=(), rgb_pin=None, rgb_count=0, rgb_fill=None):
        self.i2c = i2c
        self.addr = addr
        self.buttons = buttons
        self.num_encoders = num_encoders
        self.enc_buttons = enc_buttons
        self.analog = analog
        # keymaps placeholders
        self.key_map = None
        self.enc_map = None
        self.analog_map = None
        # handlers placeholders
        self.buttons_handler = None
        self.encoders_handler = None
        self.analog_handler = None
        self.handlers_reinit = False
        # rgb stuff on the module side
        self.rgb = None
        self.rgb_pin = rgb_pin
        self.rgb_count = rgb_count
        self.rgb_fill = rgb_fill

        try:
            self.seesaw = Seesaw(self.i2c, self.addr)
        except Exception as e:
            self.seesaw = None
            print(f"Seesaw initialization error: {e}")
        
    def set_rgb(self):
        if self.rgb_pin is not None:
            self.rgb = neopixel.NeoPixel(self.seesaw, self.rgb_pin, self.rgb_count, auto_write = True)
            self.rgb.brightness = 0.5
            self.rgb.fill(self.rgb_fill)
            self.rgb.show()
            
    def module_power_up(self):
        # Set interrupt and inputs for the seesaw device
        if self.encoders_handler:
            self.encoders_handler.set_interrupts(self.num_encoders)

        if self.buttons_handler:
            self.buttons_handler.set_interrupts()

        if self.analog_handler:
            self.analog_handler.set_analog()
        
        self.set_rgb()
        
        # Set first boot flag using the SERCOM register
        self.seesaw.uart_set_baud(11250)
        print(f"Module {hex(self.addr)} just powered up.")
    
    def read_boot_flag(self):
        buf = bytearray(4)
        self.seesaw.read(0x02, 0x04, buf)
        ret = struct.unpack(">I", buf)[0]
        if ret == 9600:
            return True
        return False
    
    def on_encoder_turn_do(self, keyboard, encoder_id, state):
        layer_id = keyboard.active_layers[0]
        # if Left, key index 0 else key index 1
        if state['direction'] == -1:
            key_index = 0
        else:
            key_index = 1
        key = self.enc_map[layer_id][encoder_id][key_index]
        keyboard.tap_key(key)
    
    def on_encoder_button_do(self, keyboard, encoder_id, state):
        if state['is_pressed'] is True:
            layer_id = keyboard.active_layers[0]
            key = self.enc_map[layer_id][encoder_id][2]
            keyboard.tap_key(key)
    
    def on_button_press_do(self, keyboard, idx):
        layer_id = keyboard.active_layers[0]
        key = self.key_map[layer_id][idx]
        keyboard.tap_key(key)
    
    def on_analog_change_do(self, keyboard, idx, value):
        cc_val = int(map_range(value, 0, 1023, 0, 127))
        self.midi.send(ControlChange(self.analog_map[idx], cc_val))
        keyboard.draw_module_activity()

    def during_bootup(self, keyboard):
        
        if self.addr not in keyboard.known_devices:
            keyboard.known_devices.append(self.addr)
        
        if self.seesaw:
            try:

                # Initialize encoders handler
                if self.enc_map and self.num_encoders > 0:
                    self.encoders_handler = OcreebEncoders(
                        seesaw=self.seesaw, 
                        num_encoders=self.num_encoders, 
                        enc_buttons=self.enc_buttons, 
                        keyboard=keyboard, 
                        on_move_callback=self.on_encoder_turn_do, 
                        on_button_callback=self.on_encoder_button_do
                    )

                # Initialize buttons handler
                if self.key_map and self.buttons:
                    self.buttons_handler = OcreebButtons(
                        seesaw=self.seesaw, 
                        buttons=self.buttons,
                        on_button_callback=lambda x: self.on_button_press_do(keyboard, x)
                    )

                # Initialize analog handler
                if self.analog_map and self.analog:
                    self.analog_handler = OcreebAnalog(
                        seesaw=self.seesaw, 
                        analog_pins=self.analog,
                        on_analog_change_callback=lambda x, y: self.on_analog_change_do(keyboard, x, y)
                    )
                    # Set midi to send control notes for anlog devices
                    self.midi = adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=0)

                # Set module interrupts, rgb and first boot flag
                self.module_power_up()

                # Make sure the handlers init flag is set back to False if this is called later
                self.handlers_reinit = False
        
            except Exception as e:
                print(f"Handlers initialization error: {e}")

    def process_interrupt(self):
        if self.seesaw:
            try:
                    
                # Check if this is a first boot interrupt by reading the SERCOM baudrate register
                if self.read_boot_flag():
                    self.module_power_up()
                    return
                
                # Check and update the different handlers
                # Update the state of the encoders
                if self.encoders_handler:
                    self.encoders_handler.update_encoders()

                # Update the state of the buttons
                if self.buttons_handler:
                    self.buttons_handler.update_buttons()

                # Clear GPIO interrupt flag
                self.seesaw.get_GPIO_interrupt_flag()

            except OSError as e:
                if e.errno == 19:
                    print(f"Module on {hex(self.addr)} not found.")
                
        else:
            print(f"No Seesaw instance on {hex(self.addr)}")
            try:
                # Reinitiate the Seesaw instance if the module atached after the controller power up
                self.seesaw = Seesaw(self.i2c, self.addr)
                self.handlers_reinit = True
                
            except Exception as e:
                print(f"Seesaw initialization error: {e}")
        
    def before_matrix_scan(self, keyboard):
        # Check if we need to reinit the handlers
        if self.handlers_reinit:
            self.during_bootup(keyboard)

    def after_matrix_scan(self, keyboard):
        return

    def on_runtime_enable(self, keyboard):
        return

    def on_runtime_disable(self, keyboard):
        return
    
    def before_hid_send(self, keyboard):
        return

    def after_hid_send(self, keyboard):
        return

    def on_powersave_enable(self, keyboard):
        return

    def on_powersave_disable(self, keyboard):
        return