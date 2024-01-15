"""
This file is adapted from Tonasz's display.py in https://github.com/Tonasz/kmk_firmware/blob/display/kmk/extensions/display.py 
Modification is noted in the subclass below.

Thanks to Tonasz for their contribution.
"""
from supervisor import ticks_ms

import adafruit_displayio_ssd1306
import displayio
import terminalio
from adafruit_display_text import label

from kmk.extensions import Extension
from kmk.handlers.stock import passthrough as handler_passthrough
from kmk.keys import make_key


class Display(Extension):
    I2C_ADDRESS = 0x3C

    def __init__(
        self, i2c, scenes, *, width=128, height=64, rotation=0, address=I2C_ADDRESS
    ):

        display_bus = displayio.I2CDisplay(i2c, device_address=address)
        self.width = width
        self.height = height
        self._display = adafruit_displayio_ssd1306.SSD1306(
            display_bus, width=width, height=height, rotation=rotation
        )
        self._scenes = scenes
        self._current_scene = 0
        self._redraw_forced = False
        self._asleep = False
        self.polling_interval = 100
        self._last_tick = ticks_ms()

        make_key(
            names=('OLED_NXT',),
            on_press=self._tb_next_scene,
            on_release=handler_passthrough,
        )

        make_key(
            names=('OLED_PRV',),
            on_press=self._tb_prev_scene,
            on_release=handler_passthrough,
        )

        make_key(
            names=('OLED_TOG',),
            on_press=self._tb_toggle,
            on_release=handler_passthrough,
        )

    def during_bootup(self, keyboard):
        self._redraw_forced = True
        for scene in self._scenes:
            scene.initialize(self, keyboard)
        self._display.show(self._get_active_scene().scene_group)

    def before_matrix_scan(self, keyboard):
        pass

    def after_matrix_scan(self, keyboard):
        pass

    def before_hid_send(self, keyboard):
        pass

    def after_hid_send(self, keyboard):
        if self._asleep:
            return

        scene = self._get_active_scene()
        now = ticks_ms()
        ready = (
            now - self._last_tick >= scene.polling_interval
        ) and scene.is_redraw_needed(keyboard)
        if self._redraw_forced or ready:
            if self._redraw_forced:
                scene.forced_draw(self, keyboard)
            else:
                scene.draw(self, keyboard)
            self._redraw_forced = False
            self._last_tick = now
        return

    def on_runtime_enable(self, keyboard):
        pass

    def on_runtime_disable(self, keyboard):
        pass

    def on_powersave_enable(self, keyboard):
        pass

    def on_powersave_disable(self, keyboard):
        pass

    def _get_active_scene(self):
        if len(self._scenes) > self._current_scene:
            return self._scenes[self._current_scene]

    def _tb_next_scene(self, *args, **kwargs):
        self._current_scene += 1
        if self._current_scene >= len(self._scenes):
            self._current_scene = 0
        self._redraw_forced = True
        self._display.show(self._get_active_scene().scene_group)

    def _tb_prev_scene(self, *args, **kwargs):
        self._current_scene -= 1
        if self._current_scene < 0:
            self._current_scene = len(self._scenes) - 1
        self._redraw_forced = True
        self._display.show(self._get_active_scene().scene_group)

    def _tb_toggle(self, *args, **kwargs):
        if self._asleep:
            self._asleep = False
            self._redraw_forced = True
            self._display.wake()
        else:
            self._asleep = True
            self._display.sleep()


class DisplayScene:
    '''Abstract class, which all other scenes depends on'''

    polling_interval = 40

    def is_redraw_needed(self, sandbox):
        '''Obligatory check, if we can skip draw logic.
        It was more important when module was based on framebuf.'''
        raise NotImplementedError

    def initialize(self, oled, sandbox):
        '''Called once during_bootup'''
        self.scene_group = None

    def forced_draw(self, oled, sandbox):
        '''Method called when draw is forced, ie when scene is changed.
        It was more important when module was based on framebuf, now maybe obsolete.'''
        self.draw(oled, sandbox)

    def draw(self, oled, sandbox):
        '''Obligatory function, defines main scene logic. Happens not more often than polling_interval.'''
        raise NotImplementedError


class BitmapLogoScene(DisplayScene):
    '''Displays bitmap from storage'''

    def __init__(self, path):
        self._path = path

    def is_redraw_needed(self, sandbox):
        return False

    def initialize(self, oled, sandbox):
        self.scene_group = displayio.Group()

        bitmap = displayio.OnDiskBitmap(self._path)
        tile_grid = displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader)
        self.scene_group.append(tile_grid)

    def draw(self, oled, sandbox):
        pass


from kmk.extensions.rgb import AnimationModes


class StatusScene(DisplayScene):
    '''Displays basic status info: current layer, default layer, rgb mode (optional)'''

    last_layer = 0
    last_rgb_mode = 0

    def __init__(
        self, *, layers_names=None, separate_default_layer=False, rgb_ext=None
    ):
        self.layers_names = layers_names
        self.separate_default_layer = separate_default_layer
        self.rgb_ext = rgb_ext

    def is_redraw_needed(self, sandbox):
        if self.last_layer != sandbox.active_layers[0]:
            self.last_layer = sandbox.active_layers[0]
            return True
        if self.rgb_ext and self.last_rgb_mode != self.rgb_ext.animation_mode:
            self.last_rgb_mode = self.rgb_ext.animation_mode
            return True
        return False

    def initialize(self, oled, sandbox):
        scene_height = 20 if self.rgb_ext is None else 30
        y_pos = int((oled.height - scene_height) / 2)
        self.scene_group = displayio.Group(x=5, y=y_pos)
        self.upper_layout_text = label.Label(
            terminalio.FONT, text=" " * 40, color=0xFFFFFF
        )
        self.scene_group.append(self.upper_layout_text)
        self.lower_layout_text = label.Label(
            terminalio.FONT, text=" " * 40, color=0xFFFFFF
        )
        self.lower_layout_text.y = 10
        self.scene_group.append(self.lower_layout_text)
        self.rgb_text = label.Label(terminalio.FONT, text=" " * 40, color=0xFFFFFF)
        self.rgb_text.y = 20
        self.scene_group.append(self.rgb_text)

    def forced_draw(self, oled, sandbox):
        self.draw(oled, sandbox)

    def draw(self, oled, sandbox):
        # add layer text
        if len(sandbox.active_layers) > 1:
            layout_def = sandbox.active_layers[len(sandbox.active_layers) - 1]
            if self.separate_default_layer:
                self.upper_layout_text.text = self._get_layer_name(self.last_layer)
                self.lower_layout_text.text = self._get_layer_name(layout_def)
            else:
                self.upper_layout_text.text = ""
                self.lower_layout_text.text = self._get_layer_name(self.last_layer)
        else:
            self.upper_layout_text.text = ""
            self.lower_layout_text.text = self._get_layer_name(self.last_layer)
        # add RGB mode text
        if self.rgb_ext is not None:
            self.rgb_text.text = f'RGB: {self._get_rgb_mode_name(self.last_rgb_mode)}'

    def _get_layer_name(self, layer_no):
        if self.layers_names is None or layer_no >= len(self.layers_names):
            return f"Layer {layer_no}"
        return self.layers_names[layer_no]

    def _get_rgb_mode_name(self, rgb_mode):
        if rgb_mode == AnimationModes.OFF:
            return 'Off mode'
        if (
            rgb_mode == AnimationModes.STATIC
            or rgb_mode == AnimationModes.STATIC_STANDBY
        ):
            return 'Static'
        elif rgb_mode == AnimationModes.BREATHING:
            return 'Breathing'
        elif rgb_mode == AnimationModes.RAINBOW:
            return 'Rainbow'
        elif rgb_mode == AnimationModes.BREATHING_RAINBOW:
            return 'Breath. rainbow'
        elif rgb_mode == AnimationModes.KNIGHT:
            return 'Knight'
        elif rgb_mode == AnimationModes.SWIRL:
            return 'Swirl'
        elif rgb_mode == AnimationModes.USER:
            return 'User'
        else:
            return 'other'


from bitmaptools import draw_line, fill_region


class KeypressesScene(DisplayScene):
    '''Displays keypresses as dots in corresponding place of rectangle symbolizing keyboard'''

    polling_interval = 0

    def __init__(self, matrix_width, matrix_height, split=False, keymap=None):
        self._matrix_width = matrix_width
        self._matrix_height = matrix_height
        self._split = split
        self._keymap = keymap
        self._size = 6

    def is_redraw_needed(self, sandbox):
        if sandbox.matrix_update or sandbox.secondary_matrix_update:
            return True
        return False

    def initialize(self, oled, sandbox):
        full_width = self._matrix_width * self._size + self._size
        if self._split:
            full_width += 2 * self._size
        full_height = self._matrix_height * self._size + self._size
        x_pos = int((oled.width - full_width) / 2)
        y_pos = int((oled.height - full_height) / 2)

        self.scene_group = displayio.Group(x=x_pos, y=y_pos)
        self._bitmap = displayio.Bitmap(oled.width, oled.height, 1)
        palette = displayio.Palette(2)
        palette[0] = 0x000000
        palette[1] = 0xFFFFFF
        tile_grid = displayio.TileGrid(self._bitmap, pixel_shader=palette)
        self.scene_group.append(tile_grid)

        if not self._split:
            self._draw_rect(0, 0, full_width, full_height, 1)
            pass
        else:
            half_width = int(self._matrix_width * self._size / 2)
            self._draw_rect(0, 0, half_width + self._size, full_height, 1)
            self._draw_rect(
                half_width + 2 * self._size, 0, half_width + self._size, full_height, 1
            )

    def forced_draw(self, oled, sandbox):
        return

    def draw(self, oled, sandbox):
        if not sandbox.matrix_update and not sandbox.secondary_matrix_update:
            return
        change = sandbox.matrix_update or sandbox.secondary_matrix_update
        (x, y) = self._get_pos(change.key_number)
        if x is None or y is None:
            return
        self._draw_key(x, y, change.pressed)
        # todo: unfortunately there is a bug with non-target side - it misses keypresses
        return

    def _draw_key(self, col, row, status):
        x = int(col * self._size + self._size / 2)
        if self._split and col >= self._matrix_width / 2:
            x += self._size * 2
        y = int(row * self._size + self._size / 2)
        self._draw_rect(x, y, self._size, self._size, status, True)
        return

    def _get_pos(self, key):
        width = self._matrix_width if not self._split else self._matrix_width / 2
        y = key // width
        x = key - (y * width)
        if self._split and y >= self._matrix_height:
            y -= self._matrix_height
            x = 2 * width - x - 1
        return (x, y)

    def _draw_rect(self, x, y, width, height, color, fill=False):
        if fill:
            fill_region(self._bitmap, x, y, x + width, y + height, color)
        else:
            draw_line(self._bitmap, x, y, x + width, y, color)
            draw_line(self._bitmap, x, y, x, y + height, color)
            draw_line(self._bitmap, x, y + height, x + width, y + height, color)
            draw_line(self._bitmap, x + width, y, x + width, y + height, color)


"""
In addition to Tonasz's OLED extension, this modification draws a small arrow in the top right corner of the OLED. 
This arrow appears for 700ms to signal an interrupt trigger from external modules.
"""

class OcreebDisplay(Display):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.arrow_shown_time = None
        self.arrow_duration_ms = 700  # Duration to show the arrow in ms

        self.arrow_bitmap = displayio.OnDiskBitmap('/ocreeb/bmp/arrow.bmp')
        self.arrow_tilegrid = displayio.TileGrid(self.arrow_bitmap, pixel_shader=self.arrow_bitmap.pixel_shader)
        self.arrow_tilegrid.x = self._display.width - self.arrow_bitmap.width - 5
        self.arrow_tilegrid.y = 0

    def draw_temp_arrow(self):
        if self.arrow_shown_time is None:
            # Add the TileGrid to the display
            self._get_active_scene().scene_group.append(self.arrow_tilegrid)
            self._display.refresh()
            self.arrow_shown_time = ticks_ms()

    def before_matrix_scan(self, keyboard):
        current_time = ticks_ms()
        if self.arrow_shown_time and (current_time - self.arrow_shown_time) >= self.arrow_duration_ms:
            # Remove the TileGrid from the display
            if self.arrow_tilegrid in self._get_active_scene().scene_group:
                self._get_active_scene().scene_group.remove(self.arrow_tilegrid)
                self._display.refresh()
            self.arrow_shown_time = None