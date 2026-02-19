#!/usr/bin/env python3
import gi, os, psutil, cairo, subprocess
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk, GdkPixbuf

# =========================
# BASE DIR (pour Flatpak)
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# =========================
# GPU DETECTION (AMD / NVIDIA)
# =========================
def get_amd_gpu_percent():
    try:
        with open("/sys/class/drm/card0/device/gpu_busy_percent", "r") as f:
            return int(f.read().strip()) / 100.0
    except:
        return None

def get_nvidia_gpu_percent():
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
            stderr=subprocess.DEVNULL
        )
        return int(output.decode().strip()) / 100.0
    except:
        return None

def get_gpu_percent():
    n = get_nvidia_gpu_percent()
    if n is not None:
        return n
    a = get_amd_gpu_percent()
    if a is not None:
        return a
    return 0.0

# =========================
# LOAD IMAGES
# =========================
def load_lifebar_images(folder):
    images = []
    for i in range(21):
        path = os.path.join(folder, f"lifebar_{i}.png")
        if os.path.exists(path):
            images.append(GdkPixbuf.Pixbuf.new_from_file(path))
        else:
            print(f"Image manquante: {path}")
    return images

# =========================
# DRAW TEXT WITH SPACING
# =========================
def draw_text_with_spacing(cr, text, x, y, spacing=2):
    for char in text:
        cr.show_text(char)
        xbearing, ybearing, width, height, xadvance, yadvance = cr.text_extents(char)
        x += width + spacing
        cr.move_to(x, y)

# =========================
# HUD BAR
# =========================
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
        index = min(percent // 5, len(self.images)-1)
        return self.images[index]

    def on_draw(self, widget, cr):
        alloc = self.get_allocation()
        w, h = alloc.width, alloc.height

        image = self.get_current_image()
        if image:
            scaled = image.scale_simple(w, h, GdkPixbuf.InterpType.BILINEAR)
            Gdk.cairo_set_source_pixbuf(cr, scaled, 0, 0)
            cr.paint()

        cr.set_source_rgb(1,1,1)
        cr.select_font_face("SAO UI TT", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(h*0.5)
        x, y = 22, h*0.7
        cr.move_to(x, y)
        draw_text_with_spacing(cr, self.label, x, y, spacing=self.letter_spacing)

# =========================
# MAIN WINDOW
# =========================
class MainWindow(Gtk.Window):
    def __init__(self):
        super().__init__()
        BASE_WIDTH = 440
        BASE_HEIGHT = 40
        SMALL_WIDTH = int(BASE_WIDTH*0.66)
        SMALL_HEIGHT = int(BASE_HEIGHT*0.66)

        self.keep_mode = "below"

        self.set_title("SAO HUD")
        self.set_decorated(False)
        self.set_keep_below(True)
        self.set_app_paintable(True)
        self.set_accept_focus(False)
        self.stick()

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)

        # LOAD IMAGES
        self.images = load_lifebar_images(os.path.join(BASE_DIR,"lifebars"))
        self.button_on_path = os.path.join(BASE_DIR,"lifebars/button_on.png")
        self.button_off_path = os.path.join(BASE_DIR,"lifebars/button_off.png")

        # FIXED LAYOUT
        self.fixed = Gtk.Fixed()
        self.add(self.fixed)

        # BARRES
        self.ram_bar = HUDBar("    RAM", self.images, BASE_WIDTH, BASE_HEIGHT)
        self.fixed.put(self.ram_bar, 40,0)

        self.gpu_bar = HUDBar("GPU", self.images, SMALL_WIDTH, SMALL_HEIGHT)
        self.fixed.put(self.gpu_bar, 40, BASE_HEIGHT+10)

        self.cpu_bar = HUDBar("CPU", self.images, SMALL_WIDTH, SMALL_HEIGHT)
        self.fixed.put(self.cpu_bar, 40, BASE_HEIGHT+10+SMALL_HEIGHT+10)

        self.ssd_bar = HUDBar("SSD", self.images, SMALL_WIDTH, SMALL_HEIGHT)
        self.fixed.put(self.ssd_bar, 40, BASE_HEIGHT+10+2*(SMALL_HEIGHT+10))

        # =========================
        # TOGGLE BUTTON
        # =========================
        self.toggle_button = Gtk.Button()
        self.toggle_button.set_size_request(20,20)
        self.toggle_button.set_relief(Gtk.ReliefStyle.NONE)
        self.toggle_button.set_focus_on_click(False)
        self.toggle_button.set_app_paintable(True)
        self.toggle_button.connect("clicked", self.toggle_keep_mode)
        self.fixed.put(self.toggle_button, 22, 3)
        self.update_button_image()

        self.show_all()
        self.move(0,40)
        GLib.timeout_add(300,self.update)

    # =========================
    # UPDATE BUTTON IMAGE
    # =========================
    def update_button_image(self):
        path = self.button_on_path if self.keep_mode=="above" else self.button_off_path
        if os.path.exists(path):
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)
            pixbuf = pixbuf.scale_simple(20,20,GdkPixbuf.InterpType.BILINEAR)
            self.toggle_button.set_image(Gtk.Image.new_from_pixbuf(pixbuf))

    # =========================
    # TOGGLE ABOVE/BELOW
    # =========================
    def toggle_keep_mode(self, button):
        if self.keep_mode=="below":
            self.set_keep_below(False)
            self.set_keep_above(True)
            self.keep_mode="above"
        else:
            self.set_keep_above(False)
            self.set_keep_below(True)
            self.keep_mode="below"
        self.update_button_image()

    # =========================
    # UPDATE VALUES
    # =========================
    def update(self):
        self.cpu_bar.value = psutil.cpu_percent()/100.0
        self.gpu_bar.value = get_gpu_percent()
        self.ram_bar.value = psutil.virtual_memory().percent/100.0
        self.ssd_bar.value = psutil.disk_usage("/").percent/100.0

        self.cpu_bar.queue_draw()
        self.gpu_bar.queue_draw()
        self.ram_bar.queue_draw()
        self.ssd_bar.queue_draw()
        return True

# =========================
# MAIN
# =========================
if __name__=="__main__":
    win = MainWindow()
    Gtk.main()
