import serial
import time
import win32api
import win32con
from serial.tools import list_ports

# ---- CONFIG ----
BAUD = 115200
SCAN_INTERVAL = 2  # seconds between rescans

# Known VID/PID of your device (FTDI FT232)
TARGET_VID = 1027      # 0x0403
TARGET_PID = 24577     # 0x6001


# ---- PORT DETECTION ----
def find_serial_port():
    print("[*] Scanning COM ports for matching VID/PID...")

    for p in list_ports.comports():
        print(f"[*] Checking {p.device}: VID={p.vid}, PID={p.pid}, Desc={p.description}")

        if p.vid == TARGET_VID and p.pid == TARGET_PID:
            print(f"[+] Found target device on {p.device}")
            try:
                ser = serial.Serial(p.device, BAUD, timeout=1)
                time.sleep(0.2)
                return ser
            except Exception as e:
                print(f"[!] Error opening {p.device}: {e}")
                return None

    print("[!] No matching device found.")
    return None


# ---- KEYBOARD INJECTION FUNCTIONS ----
def key_press(vk):
    win32api.keybd_event(vk, 0, 0, 0)
    time.sleep(0.05)
    win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)


def type_text(s):
    for ch in s:
        vk = win32api.VkKeyScan(ch)
        vk_code = vk & 0xFF

        shift_required = (vk >> 8) & 1
        if shift_required:
            win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)

        key_press(vk_code)

        if shift_required:
            win32api.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)


# ---- MAIN LOOP ----
ser = None

while True:
    # Acquire a port if we don't have one
    if ser is None:
        ser = find_serial_port()
        if ser:
            print(f"[+] Connected to {ser.port} @ {BAUD}")
        else:
            time.sleep(SCAN_INTERVAL)
            continue

    # Try reading from the port
    try:
        line = ser.readline().decode(errors='ignore').strip()
    except Exception:
        print("[!] Lost connection. Re-scanning...")
        ser = None
        time.sleep(SCAN_INTERVAL)
        continue

    if not line:
        continue

    print("RX:", line)

    # ---- COMMAND HANDLING ----
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
