"""
APEX STUDIO LAUNCHER
Build to .exe: pip install pyinstaller
Then run: pyinstaller --onefile --windowed --name "ApexStudio" launcher.py
"""
import webbrowser
import tkinter as tk
from tkinter import ttk
import threading
import time
import sys
import os

SITE_URL = "https://apex-executor.vercel.app"  # Change to your Vercel URL

class ApexLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Apex Studio Launcher")
        self.root.geometry("480x320")
        self.root.resizable(False, False)
        self.root.configure(bg="#0f0f1a")

        # Center window
        self.root.eval('tk::PlaceWindow . center')

        self.build_ui()

    def build_ui(self):
        # Background
        frame = tk.Frame(self.root, bg="#0f0f1a")
        frame.pack(fill="both", expand=True, padx=0, pady=0)

        # Logo
        logo = tk.Label(frame, text="APEX STUDIO",
            font=("Arial Black", 28, "bold"),
            fg="#e74c3c", bg="#0f0f1a")
        logo.pack(pady=(40,4))

        subtitle = tk.Label(frame, text="Game Platform Launcher",
            font=("Arial", 11), fg="#718096", bg="#0f0f1a")
        subtitle.pack(pady=(0,30))

        # Progress bar style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("red.Horizontal.TProgressbar",
            troughcolor="#16213e", background="#e74c3c",
            darkcolor="#e74c3c", lightcolor="#e74c3c",
            bordercolor="#1e3a5f")

        self.progress = ttk.Progressbar(frame, style="red.Horizontal.TProgressbar",
            length=360, mode='determinate')
        self.progress.pack(pady=(0,12))

        self.status = tk.Label(frame, text="Initializing...",
            font=("Arial", 9), fg="#718096", bg="#0f0f1a")
        self.status.pack()

        # Start loading
        threading.Thread(target=self.launch_sequence, daemon=True).start()

    def launch_sequence(self):
        steps = [
            (20, "Checking for updates..."),
            (45, "Connecting to Apex Studio..."),
            (70, "Loading game engine..."),
            (90, "Almost ready..."),
            (100, "Launching!"),
        ]
        for val, msg in steps:
            time.sleep(0.6)
            self.progress['value'] = val
            self.status.config(text=msg)
            self.root.update()

        time.sleep(0.3)
        webbrowser.open(SITE_URL)
        time.sleep(1)
        self.root.destroy()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ApexLauncher()
    app.run()
