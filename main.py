import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import keyboard
import sounddevice as sd
import soundfile as sf
import os
import json
import random
import threading
import time
import sys
import re
import numpy as np
import webbrowser  # Added for the clickable link

# --- DARK MODE COLORS ---
BG_MAIN = "#1E1E1E"
BG_SEC = "#252526"
FG_MAIN = "#D4D4D4"
ACCENT = "#007ACC"
BTN_BG = "#3E3E42"
BTN_ACTIVE = "#505050"
WARN_FG = "#F44336"


class JacketSoundboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Jacket's Tape Recorder - By a_41 ")
        self.geometry("650x750")  # Made slightly taller to fit the tutorial
        self.resizable(False, False)
        self.configure(bg=BG_MAIN)

        self.setup_theme()

        # Paths
        if getattr(sys, 'frozen', False):
            self.base_path = os.path.dirname(sys.executable)
        else:
            self.base_path = os.path.dirname(os.path.abspath(__file__))

        self.audio_dir = os.path.join(self.base_path, "AudioClip")
        self.noise_dir = os.path.join(self.audio_dir, "1. Recorder Noise")
        self.config_file = os.path.join(self.base_path, "jacket_binds.json")

        # Data
        self.categories = {}
        self.recorder_noises = []
        self.display_categories_renumbered = []
        self.sorted_original_categories_numeric = []
        self.current_listbox_paths = []

        # UI Trackers (to instantly update text to "NONE" when clearing binds)
        self.tab1_hk_vars = {}
        self.tab2_hk_var = None
        self.active_hotkeys_state = {}  # Tracks if a hotkey is currently being held down

        # Available Audio Devices
        self.output_devices = self.get_output_devices()

        # Configuration including audio settings
        self.config = {
            "tab1": {},
            "tab2": {},
            "audio": {
                "device_id": None,
                "volume": 100  # 0 to 100 scale
            }
        }

        self.current_sequence_id = 0

        self.load_directories()
        self.load_config()
        self.build_ui()
        self.bind_all_hotkeys()

    def setup_theme(self):
        """Applies a custom dark theme to the ttk widgets."""
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(".", background=BG_MAIN, foreground=FG_MAIN, font=("Helvetica", 10))
        style.configure("TNotebook", background=BG_MAIN, borderwidth=0)
        style.configure("TNotebook.Tab", background=BG_SEC, foreground=FG_MAIN, padding=[15, 5], borderwidth=0)
        style.map("TNotebook.Tab", background=[("selected", ACCENT)])
        style.configure("TFrame", background=BG_MAIN)
        style.configure("TLabel", background=BG_MAIN, foreground=FG_MAIN)
        style.configure("Header.TLabel", font=("Helvetica", 16, "bold"), foreground="#FFFFFF")
        style.configure("Hotkey.TLabel", font=("Helvetica", 10, "bold"), foreground=ACCENT)
        style.configure("Warning.TLabel", font=("Helvetica", 11), foreground=WARN_FG)
        style.configure("TButton", background=BTN_BG, foreground=FG_MAIN, borderwidth=0, padding=5, focuscolor=ACCENT)
        style.map("TButton", background=[("active", BTN_ACTIVE), ("pressed", ACCENT)])
        style.configure("Danger.TButton", background="#8B0000", foreground="#FFFFFF")
        style.map("Danger.TButton", background=[("active", "#FF0000"), ("pressed", "#FF0000")])
        style.configure("TCombobox", fieldbackground=BG_SEC, background=BTN_BG, foreground="#FFFFFF", borderwidth=0)
        style.configure("Vertical.TScrollbar", background=BTN_BG, bordercolor=BG_MAIN, arrowcolor=FG_MAIN,
                        troughcolor=BG_MAIN)
        style.configure("Horizontal.TScale", background=BG_MAIN, troughcolor=BG_SEC)
        style.configure("TLabelframe", background=BG_MAIN, foreground=FG_MAIN, bordercolor=BG_SEC)
        style.configure("TLabelframe.Label", background=BG_MAIN, foreground=FG_MAIN, font=("Helvetica", 10, "bold"))

    # --- DEVICE MANAGEMENT ---

    def get_output_devices(self):
        devices = []
        try:
            default_api = sd.default.hostapi
            for i, dev in enumerate(sd.query_devices()):
                if dev['max_output_channels'] > 0 and dev['hostapi'] == default_api:
                    devices.append((i, dev['name']))
        except Exception as e:
            print(f"Error querying devices: {e}")
        return devices

    # --- FILE & CONFIG MANAGEMENT ---

    def load_directories(self):
        if not os.path.exists(self.audio_dir):
            os.makedirs(self.audio_dir)

        if os.path.exists(self.noise_dir):
            self.recorder_noises = [os.path.join(self.noise_dir, f)
                                    for f in os.listdir(self.noise_dir) if
                                    f.lower().endswith(('.wav', '.mp3', '.ogg', '.flac'))]

        temp_renumbered = []
        temp_original = []

        for folder_name in os.listdir(self.audio_dir):
            folder_path = os.path.join(self.audio_dir, folder_name)

            if os.path.isdir(folder_path) and folder_name != "1. Recorder Noise":
                match = re.match(r'^(\d+)\.\s*(.*)$', folder_name)
                if match:
                    original_num = int(match.group(1))
                    name_part = match.group(2)

                    files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if
                             f.lower().endswith(('.wav', '.mp3', '.ogg', '.flac'))]
                    if files:
                        self.categories[folder_name] = files

                        new_num = original_num - 1
                        temp_renumbered.append({
                            "new_num": new_num,
                            "display_name": f"{new_num}. {name_part}",
                            "original_folder": folder_name
                        })
                        temp_original.append((original_num, folder_name))

        self.display_categories_renumbered = sorted(temp_renumbered, key=lambda x: x["new_num"])
        self.sorted_original_categories_numeric = [x[1] for x in sorted(temp_original)]

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    saved_config = json.load(f)
                    self.config["tab1"] = saved_config.get("tab1", {})
                    self.config["tab2"] = saved_config.get("tab2", {})
                    self.config["audio"] = saved_config.get("audio", {"device_id": None, "volume": 100})
            except Exception:
                pass

        for cat in self.categories.keys():
            if cat not in self.config["tab1"]:
                self.config["tab1"][cat] = ""
        self.save_config()

    def save_config(self):
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=4)

    # --- AUDIO PLAYBACK LOGIC ---

    def play_audio_file(self, file_path):
        try:
            data, fs = sf.read(file_path, dtype='float32')
            vol_multiplier = self.config["audio"].get("volume", 100) / 100.0
            data = data * vol_multiplier
            dev_id = self.config["audio"].get("device_id")

            sd.play(data, fs, device=dev_id)
            sd.wait()
        except Exception as e:
            print(f"Playback error: {e}")

    def play_random_from_category(self, category_name):
        if category_name in self.categories and self.categories[category_name]:
            voice_file = random.choice(self.categories[category_name])
            self.trigger_audio_sequence(voice_file)

    def trigger_audio_sequence(self, voice_path):
        self.current_sequence_id += 1
        seq_id = self.current_sequence_id

        if len(self.recorder_noises) >= 2:
            noise1, noise2 = random.sample(self.recorder_noises, 2)
        elif self.recorder_noises:
            noise1 = noise2 = self.recorder_noises[0]
        else:
            noise1 = noise2 = None

        def sequence_task():
            sd.stop()

            if noise1 and seq_id == self.current_sequence_id:
                self.play_audio_file(noise1)

            if seq_id == self.current_sequence_id:
                self.play_audio_file(voice_path)

            if noise2 and seq_id == self.current_sequence_id:
                self.play_audio_file(noise2)

        threading.Thread(target=sequence_task, daemon=True).start()

    # --- HOTKEY LOGIC ---

    def bind_all_hotkeys(self):
        # 1. Remove all old hooks
        keyboard.unhook_all()
        # 2. Reset the state tracker
        self.active_hotkeys_state.clear()
        
        # 3. Take a static snapshot of the config to prevent thread-crashing
        tab1_binds = list(self.config["tab1"].items())
        tab2_binds = list(self.config["tab2"].items())
        
        # 4. Create a custom global event listener
        def global_key_hook(e):
            # Check Random Binds (Tab 1)
            for cat, hk in tab1_binds:
                if hk:
                    try:
                        if keyboard.is_pressed(hk):
                            # Only trigger if it wasn't ALREADY pressed down
                            if not self.active_hotkeys_state.get(hk, False):
                                self.active_hotkeys_state[hk] = True
                                self.play_random_from_category(cat)
                        else:
                            self.active_hotkeys_state[hk] = False
                    except ValueError:
                        pass

            # Check Specific Binds (Tab 2)
            for path, hk in tab2_binds:
                if hk and os.path.exists(path):
                    try:
                        if keyboard.is_pressed(hk):
                            if not self.active_hotkeys_state.get(hk, False):
                                self.active_hotkeys_state[hk] = True
                                self.trigger_audio_sequence(path)
                        else:
                            self.active_hotkeys_state[hk] = False
                    except ValueError:
                        pass

        # 5. Attach our custom listener to run in the background
        keyboard.hook(global_key_hook)

    def record_hotkey(self, key_id, tab, label_var):
        self.attributes('-topmost', True)
        label_var.set("Press key...")
        self.update()

        new_hotkey = keyboard.read_hotkey(suppress=False)

        self.config[tab][key_id] = new_hotkey
        self.save_config()
        self.bind_all_hotkeys()

        label_var.set(new_hotkey.upper())
        self.attributes('-topmost', False)

    def delete_selected_bind(self):
        selected_indices = self.bind_listbox.curselection()
        if not selected_indices:
            return

        index = selected_indices[0]
        path_to_remove = self.current_listbox_paths[index]

        if path_to_remove in self.config["tab2"]:
            self.config["tab2"][path_to_remove] = ""

        self.save_config()
        self.bind_all_hotkeys()
        self.refresh_bind_listbox()

        if self.tab2_hk_var:
            self.tab2_hk_var.set("NONE")

    def clear_all_binds(self):
        """Wipes all binds from the config, unhooks keys, and updates the UI."""
        confirm = messagebox.askyesno("Clear All Bindings",
                                      "Are you sure you want to delete ALL your saved hotkeys?\n\nThis cannot be undone.")

        if confirm:
            for cat in self.config["tab1"]:
                self.config["tab1"][cat] = ""
                if cat in self.tab1_hk_vars:
                    self.tab1_hk_vars[cat].set("NONE")

            self.config["tab2"] = {}
            if self.tab2_hk_var:
                self.tab2_hk_var.set("NONE")

            self.save_config()
            self.bind_all_hotkeys()
            self.refresh_bind_listbox()

    # --- UI CONSTRUCTION ---

    def build_ui(self):
        if not self.categories:
            ttk.Label(self, text="No AudioClip folder found!\nPlease place the folder structure next to this script.",
                      style="Warning.TLabel", justify="center").pack(pady=50)
            return

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=15, pady=15)

        tab1 = ttk.Frame(notebook)
        notebook.add(tab1, text="  Random Binds  ")
        self.build_tab1(tab1)

        tab2 = ttk.Frame(notebook)
        notebook.add(tab2, text="  Specific Binds  ")
        self.build_tab2(tab2)

        tab3 = ttk.Frame(notebook)
        notebook.add(tab3, text=" Options  ")
        self.build_tab3(tab3)

    def build_tab1(self, parent):
        canvas = tk.Canvas(parent, bg=BG_MAIN, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)

        for cat_data in self.display_categories_renumbered:
            display_name = cat_data["display_name"]
            original_folder_key = cat_data["original_folder"]

            row = ttk.Frame(scrollable_frame, padding=5)
            row.pack(fill="x", expand=True, padx=5)

            ttk.Label(row, text=display_name, width=38, anchor="w").pack(side="left")

            hk_display = self.config["tab1"].get(original_folder_key, "").upper() or "NONE"
            hk_var = tk.StringVar(value=hk_display)
            self.tab1_hk_vars[original_folder_key] = hk_var

            ttk.Label(row, textvariable=hk_var, width=15, style="Hotkey.TLabel").pack(side="left")

            ttk.Button(row, text="Bind Key",
                       command=lambda c=original_folder_key, v=hk_var: self.record_hotkey(c, "tab1", v), width=10).pack(
                side="left", padx=5)
            ttk.Button(row, text="Test Random", command=lambda c=original_folder_key: self.play_random_from_category(c),
                       width=14).pack(side="left")

    def build_tab2(self, parent):
        top_frame = ttk.Frame(parent, padding=15)
        top_frame.pack(fill="x")

        ttk.Label(top_frame, text="1. Category:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        cat_combo = ttk.Combobox(top_frame, values=self.sorted_original_categories_numeric, width=50, state="readonly")
        cat_combo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(top_frame, text="2. Voice Line:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        voice_combo = ttk.Combobox(top_frame, width=50, state="readonly")
        voice_combo.grid(row=1, column=1, padx=5, pady=5)

        def update_voices(event):
            cat = cat_combo.get()
            if cat in self.categories:
                file_paths = self.categories[cat]
                voice_combo['values'] = sorted([os.path.basename(p) for p in file_paths])
                if file_paths:
                    voice_combo.current(0)
                update_hk_label(None)

        cat_combo.bind("<<ComboboxSelected>>", update_voices)

        hk_var = tk.StringVar(value="NONE")
        self.tab2_hk_var = hk_var

        ttk.Label(top_frame, text="Current Bind:").grid(row=2, column=0, sticky="w", padx=5, pady=10)
        ttk.Label(top_frame, textvariable=hk_var, style="Hotkey.TLabel").grid(row=2, column=1, sticky="w", padx=5,
                                                                              pady=10)

        def update_hk_label(event):
            cat = cat_combo.get()
            filename = voice_combo.get()
            if cat and filename:
                full_path = os.path.join(self.audio_dir, cat, filename)
                hk_var.set(self.config["tab2"].get(full_path, "").upper() or "NONE")

        voice_combo.bind("<<ComboboxSelected>>", update_hk_label)

        def bind_specific():
            cat = cat_combo.get()
            filename = voice_combo.get()
            if cat and filename:
                full_path = os.path.join(self.audio_dir, cat, filename)
                self.record_hotkey(full_path, "tab2", hk_var)

        def play_specific():
            cat = cat_combo.get()
            filename = voice_combo.get()
            if cat and filename:
                full_path = os.path.join(self.audio_dir, cat, filename)
                self.trigger_audio_sequence(full_path)

        btn_frame = ttk.Frame(top_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10, sticky="w")
        ttk.Button(btn_frame, text="Bind Hotkey", command=bind_specific, width=15).pack(side="left", padx=(5, 10))
        ttk.Button(btn_frame, text="Play Preview", command=play_specific, width=15).pack(side="left")

        ttk.Label(parent, text="Your Specific Bindings (Auto-Saved):", font=("Helvetica", 10, "bold")).pack(anchor="w",
                                                                                                            padx=20,
                                                                                                            pady=(
                                                                                                            10, 5))

        list_frame = ttk.Frame(parent)
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        self.bind_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Consolas", 10),
                                       selectmode=tk.SINGLE, bg=BG_SEC, fg=FG_MAIN, selectbackground=ACCENT,
                                       selectforeground="#ffffff", highlightthickness=0, relief="flat")
        self.bind_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.bind_listbox.yview)

        ttk.Button(parent, text="Delete Selected Bind", command=self.delete_selected_bind, width=25).pack(pady=(0, 15))

        self.refresh_bind_listbox()
        parent.bind("<Enter>", lambda e: self.refresh_bind_listbox())

    def refresh_bind_listbox(self):
        self.bind_listbox.delete(0, tk.END)
        self.current_listbox_paths = []
        for path, hk in self.config["tab2"].items():
            if hk:
                filename = os.path.basename(path)
                self.bind_listbox.insert(tk.END, f"[{hk.upper()}]  {filename}")
                self.current_listbox_paths.append(path)

    def build_tab3(self, parent):
        ttk.Label(parent, text="Audio Routing Setup", style="Header.TLabel").pack(pady=(20, 5))

        # --- TUTORIAL ---
        tutorial_text = (
            "To play sounds in-game so others can hear them:\n\n"
            "1. Install a Virtual Audio Cable.\n"
            "2. Set this app's 'Output Device' to the Virtual Cable Input.\n"
            "3. Set your game's Microphone to the Virtual Cable Output.\n\n"
            "(If you already use audio mixers like Voicemeeter or SteelSeries Sonar,\n"
            "you can simply route the output through your existing setup.)"
        )
        ttk.Label(parent, text=tutorial_text, justify="center", foreground="#AAAAAA").pack(pady=(0, 10))

        # --- CLICKABLE LINK ---
        link_font = ("Helvetica", 10, "underline")
        link_label = tk.Label(parent, text="Click here to download VB-Cable (Free)",
                              fg=ACCENT, bg=BG_MAIN, font=link_font, cursor="hand2")
        link_label.pack(pady=(0, 20))
        link_label.bind("<Button-1>", lambda e: webbrowser.open_new("https://vb-audio.com/Cable/"))

        # --- DEVICE SELECTION ---
        device_frame = ttk.Frame(parent, padding=10)
        device_frame.pack(fill="x", padx=30, pady=5)

        ttk.Label(device_frame, text="Output Device:", width=15).pack(side="left", padx=5)

        device_names = ["System Default"] + [f"{d[1]} (ID: {d[0]})" for d in self.output_devices]

        dev_combo = ttk.Combobox(device_frame, values=device_names, width=45, state="readonly")
        dev_combo.pack(side="left", padx=5)

        current_dev_id = self.config["audio"].get("device_id")
        if current_dev_id is None:
            dev_combo.current(0)
        else:
            for i, dev in enumerate(self.output_devices):
                if dev[0] == current_dev_id:
                    dev_combo.current(i + 1)
                    break

        def on_device_change(event):
            selection_idx = dev_combo.current()
            if selection_idx == 0:
                self.config["audio"]["device_id"] = None
            else:
                selected_device = self.output_devices[selection_idx - 1]
                self.config["audio"]["device_id"] = selected_device[0]
            self.save_config()

        dev_combo.bind("<<ComboboxSelected>>", on_device_change)

        # --- VOLUME CONTROL ---
        vol_frame = ttk.Frame(parent, padding=10)
        vol_frame.pack(fill="x", padx=30, pady=5)

        ttk.Label(vol_frame, text="Playback Volume:", width=15).pack(side="left", padx=5)

        current_vol = self.config["audio"].get("volume", 100)
        vol_var = tk.IntVar(value=current_vol)

        vol_slider = ttk.Scale(vol_frame, from_=0, to=100, orient="horizontal", variable=vol_var, length=250)
        vol_slider.pack(side="left", padx=10)

        vol_label = ttk.Label(vol_frame, text=f"{current_vol}%", font=("Helvetica", 10, "bold"))
        vol_label.pack(side="left", padx=10)

        def on_volume_change(event):
            vol = int(float(vol_slider.get()))
            vol_label.config(text=f"{vol}%")
            self.config["audio"]["volume"] = vol
            self.save_config()

        vol_slider.bind("<Motion>", on_volume_change)
        vol_slider.bind("<ButtonRelease-1>", on_volume_change)

        # --- DANGER ZONE ---
        danger_frame = ttk.LabelFrame(parent, text=" Reset ", padding=15)
        danger_frame.pack(fill="x", padx=35, pady=30)

        ttk.Label(danger_frame, text="Wipe all saved hotkeys from Menu 1 and Menu 2.").pack(side="left", padx=5)
        ttk.Button(danger_frame, text="Clear All Bindings", style="Danger.TButton", command=self.clear_all_binds,
                   width=18).pack(side="right", padx=5)


if __name__ == "__main__":
    app = JacketSoundboard()
    app.mainloop()
