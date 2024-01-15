# ocreeb_analog.py
from kmk.scheduler import create_task, cancel_task

class OcreebAnalog:
    def __init__(self, seesaw, analog_pins, on_analog_change_callback):
        self.seesaw = seesaw
        self.analog_pins = analog_pins
        self.change_threshold = 5 # significant change threshold
        self.on_analog_change_callback = on_analog_change_callback
        self.last_values = [0] * len(analog_pins)
        self.set_analog()
    
    def set_analog(self):
        self._task = create_task(self.update_analog, period_ms=100)
    
    def update_analog(self):
        for idx, pin in enumerate(self.analog_pins):
            try:
                current_value = self.seesaw.analog_read(pin)
                # Check for significant change
                if abs(self.last_values[idx] - current_value) > self.change_threshold:
                    # Invoke the callback function
                    self.on_analog_change_callback(idx, current_value)
                    self.last_values[idx] = current_value
            except OSError as e:
                if e.errno == 19:
                    cancel_task(self._task)