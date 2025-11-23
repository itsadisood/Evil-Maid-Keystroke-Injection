import serial
import time
import win32api
import win32con

# ---- CONFIG ----
ser = serial.Serial('COM3', 115200, timeout=1)
print("Listening on COM3 @ 115200...")

def key_press(vk):
    win32api.keybd_event(vk, 0, 0, 0)
    time.sleep(0.05)
    win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)

def type_text(s):
    for ch in s:
        vk = win32api.VkKeyScan(ch)
        vk_code = vk & 0xFF

        shift_required = vk >> 8 & 1
        if shift_required:
            win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)

        key_press(vk_code)

        if shift_required:
            win32api.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)

while True:
    line = ser.readline().decode(errors='ignore').strip()
    if not line:
        continue

    print("RX:", line)

    if line == "WINR":
        win = win32con.VK_LWIN
        win32api.keybd_event(win, 0, 0, 0)
        key_press(ord('R'))
        win32api.keybd_event(win, 0, win32con.KEYEVENTF_KEYUP, 0)

    elif line.startswith("TYPE:"):
        text = line[5:]
        type_text(text)

    elif line == "ENTER":
        key_press(win32con.VK_RETURN)
