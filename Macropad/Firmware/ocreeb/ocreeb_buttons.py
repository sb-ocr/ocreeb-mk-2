# ocreeb_buttons.py
class OcreebButtons:
    def __init__(self, seesaw, buttons, on_button_callback):
        self.seesaw = seesaw
        self.buttons = buttons
        self.button_press_callback = on_button_callback
        self.buttons_mask = self.gpio_mask(self.buttons)
        self.button_states = [False] * len(self.buttons)  # Initialize button states as 'released'
        self.set_interrupts()

    def set_interrupts(self):       
        self.seesaw.pin_mode_bulk(self.buttons_mask, self.seesaw.INPUT_PULLUP)
        self.seesaw.set_GPIO_interrupts(self.buttons_mask, True)
        self.update_buttons()

    def update_buttons(self):
        btns = self.seesaw.digital_read_bulk(self.buttons_mask)

        for idx, button_pin in enumerate(self.buttons):
            is_pressed = not (btns & (1 << button_pin))
            if is_pressed != self.button_states[idx]:  # State change detected
                if is_pressed:  # Button is pressed
                    self.button_press_callback(idx)
                self.button_states[idx] = is_pressed

    def gpio_mask(self, pins):
        mask = 0
        for pin in pins:
            mask |= 1 << pin
        return mask