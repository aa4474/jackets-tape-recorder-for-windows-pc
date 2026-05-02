# Jacket Soundboard - PC Edition 📼

A lightweight, standalone PC soundboard dedicated to Jacket from *Payday 2*. 

This project was completely rebuilt from the ground up for Windows, inspired by the original mobile Android version of the **Jacket Tape Recorder** created by **M4rkoHR** on GitHub years ago. 

**The Main Purpose:** This app is built strictly for fun and a bit of harmless trolling in online game voice chats. Why speak into a microphone when you can communicate exclusively through an 80s cassette tape recorder?

---

## 🎯 Features

* **Global Hotkeys:** Bind sounds to custom key combinations (like `Shift + S`). The sounds will trigger even when the app is minimized and you are tabbed into a game.
* **Dual Menus:**
  * **Random by Category:** Bind a key to an entire folder (e.g., "Enemy Callouts"). Pressing the hotkey plays a random voice line from that category to keep things fresh.
  * **Specific Binds:** Bind a key to one exact voice line for precise comedic timing.
* **Built-in Audio Routing:** Features a dedicated settings menu to route your audio output directly into a Virtual Audio Cable, allowing other players in your lobby to hear the soundboard through your microphone feed.
* **Dynamic UI:** You don't need to edit code to add sounds. Just drop your `.wav`, `.mp3`, or `.ogg` files into the `AudioClip` folder, and the app automatically builds the menus and categories for you.

---

## 🛠️ Installation & Setup

**All original voice lines and cassette noises are included in this release!**

1. Go to the **[Releases](../../releases)** tab and download the latest `.zip` file.
2. Extract the folder anywhere on your PC.
3. Run `Jacket's Tape Recorder v1.0.exe`. 

*Tip: If your hotkeys are not registering while you are inside a fullscreen game, close the app and run `Jacket's Tape Recorder v1.0.exe` as an Administrator.*

---

## 🎙️ How to Play Sounds in Voice Chat (For Trolling/Teammates)

If you want the game lobby to hear Jacket instead of your real voice, you need to route the application's audio into your microphone input.

1. Download and install a free virtual audio driver like **[VB-Cable](https://vb-audio.com/Cable/)**.
2. Open the soundboard app and go to **Menu 3: Audio & Options**.
3. Change the **Output Device** to `CABLE Input (VB-Audio Virtual Cable)`.
4. Open your game's audio settings (or Discord/TeamSpeak) and change your **Microphone/Input Device** to `CABLE Output (VB-Audio Virtual Cable)`.

*(If you already use audio mixing software like Voicemeeter, SteelSeries Sonar, or Wave Link, you can simply route the app's output through your existing virtual microphone setup!)*

---

## 👨‍💻 Open Source & Porting

This project is completely open-source. Anyone is free to fork the code, modify it, port it to Linux or macOS, or do whatever else you want with it! 

**To compile from source:**
1. Clone this repository.
2. Install the required Python libraries:
   `pip install -r requirements.txt`
3. Compile the standalone executable using PyInstaller:
   `pyinstaller --noconsole --onefile --icon=icon.ico main.py`

---
**Credits:** Massive shoutout to [M4rkoHR](https://github.com/M4rkoHR) for the original mobile concept that inspired this PC port.
