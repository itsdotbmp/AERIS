import os
import sys
import curses

# Windows-only console resize
if os.name == "nt":
    import ctypes
    from ctypes import wintypes

    def set_console_size(width_chars=80, height_chars=25):
        """
        Set the Windows console to a given width and height in characters.
        """
        # Get handle
        STD_OUTPUT_HANDLE = -11
        h = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)

        # Define COORD structure
        class COORD(ctypes.Structure):
            _fields_ = [("X", wintypes.SHORT), ("Y", wintypes.SHORT)]
        
        # Define SMALL_RECT structure
        class SMALL_RECT(ctypes.Structure):
            _fields_ = [("Left", wintypes.SHORT),
                        ("Top", wintypes.SHORT),
                        ("Right", wintypes.SHORT),
                        ("Bottom", wintypes.SHORT)]
        
        # Set buffer size first
        buffer_size = COORD(width_chars, height_chars)
        ctypes.windll.kernel32.SetConsoleScreenBufferSize(h, buffer_size)

        # Set window size
        rect = SMALL_RECT(0, 0, width_chars - 1, height_chars - 1)
        ctypes.windll.kernel32.SetConsoleWindowInfo(h, True, ctypes.byref(rect))

    # Call it before curses starts
    set_console_size(80, 25)


from controllers.main_menu_controller import _startup


def main():
    curses.wrapper(_startup)

if __name__ == "__main__":
    main()