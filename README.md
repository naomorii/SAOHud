
Compatibility
-----

This app has been written to work on Nobara (Fedora 42) distribution.
It is made for Gnome (49) Wayland (using XWayland), but could be used by any system that has compatibility with X11 commands.


Installation
-----

1 - Download the files.

2 - Extract the files from the archive

3 - Move the sao-hud folder to /home/YOUR_USERNAME/

To start the app manually, use the following command in the terminal :
GDK_BACKEND=x11 python3 main.py


Launch at startup
-----

1 - Copy sao-hud.desktop (from the "utils" folder) to /home/YOUR_USERNAME/.config/autostart/

2 - Edit the path to the app directory to make it readable for your system.

3 - Use the following command in the terminal to make it executable :
    chmod +x ~/.config/autostart/sao-hud.desktop

4 - Reconnect your user session to see the app launch at startup
