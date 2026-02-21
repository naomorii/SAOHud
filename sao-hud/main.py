#!/usr/bin/env python3
import gi
import os
import psutil
import cairo
import subprocess

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk, GdkPixbuf

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ==========================================================
# GPU DETECTION (AMD / NVIDIA)
# ==========================================================

def get_amd_gpu_percent():
    try:
        with open("/sys/class/drm/card0/device/gpu_busy_percent", "r") as f:
            return int(f.read().strip()) / 100.0
    except Exception:
        return None

def get_nvidia_gpu_percent():
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
            stderr=subprocess.DEVNULL
        )
        return int(output.decode().strip()) / 100.0
    except Exception:
        return None

def get_gpu_percent():
    n = get_nvidia_gpu_percent()
    if n is not None:
        return n
    a = get_amd_gpu_percent()
    if a is not None:
        return a
    return 0.0

# ==========================================================
# LOAD LIFE BAR IMAGES
# ==========================================================

def load_lifebar_images(folder):
    images = []
    for i in range(21):
        path = os.path.join(folder, f"lifebar_{i}.png")
        if os.path.exists(path):
            images.append(GdkPixbuf.Pixbuf.new_from_file(path))
        else:
            print(f"Image manquante : {path}")
    return images

# ==========================================================
# DRAW TEXT WITH LETTER SPACING
# ==========================================================

def draw_text_with_spacing(cr, text, x, y, spacing=2):
    cr.move_to(x, y)
    for char in text:
        cr.show_text(char)
        _, _, width, _, _, _ = cr.text_extents(char)
        x += width + spacing
        cr.move_to(x, y)

# ==========================================================
# HUD BAR WIDGET
# ==========================================================

class HUDBar(Gtk.DrawingArea):
    def __init__(self, label, images, width, height, letter_spacing=2):
        super().__init__()
        self.label = label
        self.images = images
        self.value = 0.0
        self.letter_spacing = letter_spacing
        self.set_size_request(width, height)
        self.connect("draw", self.on_draw)

    def get_current_image(self):
        if not self.images:
            return None
        inverted = 1.0 - self.value
        percent = int(inverted * 100)
        index = min(percent // 5, len(self.images) - 1)
        return self.images[index]

    def on_draw(self, widget, cr):
        alloc = self.get_allocation()
        w, h = alloc.width, alloc.height

        image = self.get_current_image()
        if image:
            scaled = image.scale_simple(w, h, GdkPixbuf.InterpType.BILINEAR)
            Gdk.cairo_set_source_pixbuf(cr, scaled, 0, 0)
            cr.paint()

        cr.set_source_rgb(1, 1, 1)
        cr.select_font_face("SAO UI TT", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(h * 0.5)

        draw_text_with_spacing(cr, self.label, 22, h * 0.7, self.letter_spacing)

# ==========================================================
# HUD WINDOW (CLICK-THROUGH)
# ==========================================================

class HUDWindow(Gtk.Window):
    def __init__(self):
        super().__init__()

        self.keep_mode = "below"

        BASE_WIDTH = 440
        BASE_HEIGHT = 40
        SMALL_WIDTH = int(BASE_WIDTH * 0.66)
        SMALL_HEIGHT = int(BASE_HEIGHT * 0.66)

        self.set_decorated(False)
        self.set_keep_below(True)
        self.set_app_paintable(True)
        self.set_accept_focus(False)
        self.stick()

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)

        self.images = load_lifebar_images(os.path.join(BASE_DIR, "lifebars"))

        self.fixed = Gtk.Fixed()
        self.add(self.fixed)

        self.ram_bar = HUDBar("    RAM", self.images, BASE_WIDTH, BASE_HEIGHT)
        self.fixed.put(self.ram_bar, 40, 0)

        self.gpu_bar = HUDBar("GPU", self.images, SMALL_WIDTH, SMALL_HEIGHT)
        self.fixed.put(self.gpu_bar, 40, BASE_HEIGHT + 10)

        self.cpu_bar = HUDBar("CPU", self.images, SMALL_WIDTH, SMALL_HEIGHT)
        self.fixed.put(self.cpu_bar, 40, BASE_HEIGHT + 10 + SMALL_HEIGHT + 10)

        self.ssd_bar = HUDBar("SSD", self.images, SMALL_WIDTH, SMALL_HEIGHT)
        self.fixed.put(self.ssd_bar, 40, BASE_HEIGHT + 10 + 2 * (SMALL_HEIGHT + 10))

        self.show_all()

        self.connect("map-event", self.enable_clickthrough)

        GLib.idle_add(self.force_position)
        GLib.timeout_add(300, self.update)

    def enable_clickthrough(self, *args):
        gdk_window = self.get_window()
        if not gdk_window:
            return
        region = cairo.Region()
        gdk_window.input_shape_combine_region(region, 0, 0)
        gdk_window.set_pass_through(True)

    def toggle_layer(self):
        if self.keep_mode == "below":
            self.set_keep_below(False)
            self.set_keep_above(True)
            self.keep_mode = "above"
        else:
            self.set_keep_above(False)
            self.set_keep_below(True)
            self.keep_mode = "below"

    def force_position(self):
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor()
        geometry = monitor.get_geometry()
        self.move(geometry.x, geometry.y + 40)
        return False

    def update(self):
        self.cpu_bar.value = psutil.cpu_percent() / 100.0
        self.gpu_bar.value = get_gpu_percent()
        self.ram_bar.value = psutil.virtual_memory().percent / 100.0
        self.ssd_bar.value = psutil.disk_usage("/").percent / 100.0

        self.cpu_bar.queue_draw()
        self.gpu_bar.queue_draw()
        self.ram_bar.queue_draw()
        self.ssd_bar.queue_draw()
        return True

# ==========================================================
# BUTTON WINDOW
# ==========================================================

class ButtonWindow(Gtk.Window):
    def __init__(self, hud_window):
        super().__init__()

        self.hud_window = hud_window

        self.set_decorated(False)
        self.set_keep_below(True)
        self.set_app_paintable(True)
        self.set_accept_focus(False)
        self.stick()
        self.set_size_request(30, 30)
        
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)

        self.button = Gtk.Button()
        self.button.set_size_request(20, 20)
        self.button.set_relief(Gtk.ReliefStyle.NONE)
        self.button.connect("clicked", self.toggle_keep_mode)
        self.add(self.button)

        self.button_on = os.path.join(BASE_DIR, "lifebars/button_on.png")
        self.button_off = os.path.join(BASE_DIR, "lifebars/button_off.png")

        self.update_button_image()

        self.show_all()
        GLib.idle_add(self.force_position)

    def force_position(self):
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor()
        geometry = monitor.get_geometry()
        self.move(geometry.x + 22, geometry.y + 43)
        return False

    def update_button_image(self):
        path = self.button_on if self.hud_window.keep_mode == "above" else self.button_off
        if os.path.exists(path):
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)
            pixbuf = pixbuf.scale_simple(20, 20, GdkPixbuf.InterpType.BILINEAR)
            self.button.set_image(Gtk.Image.new_from_pixbuf(pixbuf))

    def toggle_keep_mode(self, button):
        self.hud_window.toggle_layer()

        if self.hud_window.keep_mode == "above":
            self.set_keep_below(False)
            self.set_keep_above(True)
        else:
            self.set_keep_above(False)
            self.set_keep_below(True)

        self.update_button_image()

# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":
    hud = HUDWindow()
    button = ButtonWindow(hud)
    Gtk.main()
