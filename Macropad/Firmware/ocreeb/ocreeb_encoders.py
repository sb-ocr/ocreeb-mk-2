# ocreeb_encoders.py
from adafruit_seesaw import rotaryio, digitalio
from kmk.modules.encoder import I2CEncoder

class OcreebEncoder(I2CEncoder):
    def __init__(self, seesaw, button_pin, encoder_idx=0, is_inverted=False):
        super(I2CEncoder, self).__init__(is_inverted)
        self.seesaw = seesaw
        self.encoder = rotaryio.IncrementalEncoder(self.seesaw, encoder_idx)
        self.button_pin = button_pin
        
        if self.button_pin:
            self.seesaw.pin_mode(button_pin, self.seesaw.INPUT_PULLUP)
            self.switch = digitalio.DigitalIO(self.seesaw, button_pin)
        
        self._state = self.encoder.position
    
    def button_event(self):
        if not self.button_pin:
            return
        super().button_event()
    
    def get_state(self):
        return {
            'direction': self.is_inverted and -self._direction or self._direction,
            'position': self._state,
            'is_pressed': not self.switch.value if self.button_pin else None,
            'is_held': self._button_held if self.button_pin else None, 
            'velocity': self._velocity,
        }
    
class OcreebEncoders:
    def __init__(self, seesaw, num_encoders, enc_buttons, keyboard, on_move_callback, on_button_callback):
        self.encoders = []
        self.seesaw = seesaw
        self.buttons_mask = self.gpio_mask(enc_buttons) if enc_buttons else None

        for idx in range(num_encoders):
            button_pin = enc_buttons[idx] if idx < len(enc_buttons) else None
            new_encoder = OcreebEncoder(
                seesaw,
                button_pin,
                encoder_idx=idx
            )
            new_encoder.on_move_do = lambda x, bound_idx=idx: on_move_callback(keyboard, bound_idx, x)
            new_encoder.on_button_do = lambda x, bound_idx=idx: on_button_callback(keyboard, bound_idx, x) if button_pin else None

            self.encoders.append(new_encoder)

        self.set_interrupts(num_encoders)

    def set_interrupts(self, num_encoders):
        if self.buttons_mask:
            self.seesaw.pin_mode_bulk(self.buttons_mask, self.seesaw.INPUT_PULLUP)
            self.seesaw.set_GPIO_interrupts(self.buttons_mask, True)
        
        for idx in range(num_encoders):
            self.seesaw.enable_encoder_interrupt(idx)

    def update_encoders(self):
        for encoder in self.encoders:
            encoder.update_state()

    def gpio_mask(self, pins):
        mask = 0
        for pin in pins:
            mask |= 1 << pin
        return mask