# JARVIS VoiceOS — Production-Grade Windows AI Voice Assistant

Inspired by **[VoiceOS](https://www.voiceos.com/)** and the futuristic vision of Tony Stark's JARVIS, **JARVIS VoiceOS** is a system-wide desktop AI productivity layer engineered for Windows 10 & 11.

It runs quietly in the system tray, activates instantly via global hotkeys (`CTRL + ALT`), displays a dynamic **liquid-glass top-center notch HUD**, and unifies **Agent Mode** (voice-to-action desktop automation), **Dictation Mode** (intelligent system-wide typing), and **Edit/Vision Mode** (screen & error understanding).

---

## 🌟 Key Highlights

* **Dynamic Top-Center Notch HUD (VoiceOS Clone)**:
  * **Anchored Top-Center**: Sits gracefully on the active monitor above active applications without stealing keyboard focus.
  * **Dual Trigger**: Tap `CTRL + ALT` from any application (Chrome, VS Code, Notepad) or click directly on the Notch pill.
  * **Animated Waveform**: 4-band audio visualizer dynamically expands and vibrates with voice energy in real time.
  * **Action Preview Cards**: Consequential or multi-step actions display an interactive glass card with the target app icon, action details, and **Confirm** / **Cancel** buttons.
* **Crystal-Clear Neural Speech Synthesis**:
  * Powered by Microsoft Neural Voices (`en-US-BrianNeural` / `en-US-AndrewNeural`), delivering natural, high-definition audio that sounds like a real conversational assistant.
  * **Barge-In Support**: Say *"Stop"* or press `CTRL + ALT` to immediately interrupt and cancel active speech.
  * Offline fallback to Windows SAPI5 voice engine when disconnected.
* **Lightning-Fast Cloud AI & Offline Dual Engine**:
  * **Groq Cloud Engine**: Sub-second (<300ms) Llama 3 & Whisper-large-v3-turbo inference.
  * **Built-in Local Semantic Parser**: 100% offline rule-based parser that executes all desktop and browser commands with zero latency and zero API keys needed.
* **Unified VoiceOS Modes**:
  1. **Agent Mode (Voice-to-Action)**: Automates applications, Chrome, YouTube searches, window management, files, and system controls.
  2. **Dictation Mode (Voice-to-Text)**: Automatically removes filler words (*"um"*, *"like"*), fixes punctuation, and types directly into whichever window is active.
  3. **Edit / Vision Mode**: Screen and error diagnosis using on-demand screenshots and OCR.
* **Sliding History Drawer (`CTRL + ALT + H`)**:
  * Hidden drawer smoothly slides out from the left screen edge.
  * Categorized by **Today**, **Yesterday**, and **Earlier**.
  * Instant search, **Run Again**, **Copy to Clipboard**, and **Delete**.

---

## 🚀 Quick Start

### 1. Requirements
* Windows 10 or 11 (64-bit)
* Python 3.10+ (Python 3.13 verified)

### 2. Installation
```powershell
git clone https://github.com/rahulachari/rahulachari.github.io.git
cd "AGENT JARVIS 1.0"
pip install -r requirements.txt
```

### 3. Running JARVIS
```powershell
python run.py
```
JARVIS will start silently in the Windows system tray with the compact top-center Notch HUD ready.

---

## 🎙️ Global Hotkeys & Shortcuts

| Shortcut | Description |
| :--- | :--- |
| **`CTRL + ALT`** | **Primary Wake Key**: Expands the Notch HUD and begins listening. If JARVIS is speaking, acts as a **barge-in interrupt** to stop speech immediately. |
| **Click on Notch** | Directly toggles voice recording on/off. |
| **`CTRL + ALT + H`** | **History Drawer**: Toggles the sliding history sidebar from the left screen edge. |

---

## 🗣️ Supported Voice Commands

### 🌐 Chrome & YouTube Automation
* *"Open YouTube"*
* *"Search YouTube for Python AI tutorials"*
* *"Search Google for quantum computing"*
* *"Scroll down"* / *"Scroll up"*
* *"Open new tab"* / *"Close tab"* / *"Refresh page"*
* *"Go back"* / *"Go forward"*

### 💻 Windows Desktop Automation
* *"Open Notepad"* / *"Launch Calculator"*
* *"Open Task Manager"* / *"Launch VS Code"* / *"Open Settings"*
* *"Switch to VS Code"* / *"Focus Chrome"*
* *"Minimize this window"* / *"Maximize this window"*
* *"Lock my PC"*
* *"Volume up"* / *"Volume down"* / *"Mute"*

### 📁 File System Operations
* *"Find my resume"*
* *"Open my notes"*
* *"Create a folder called Projects"*
* *"Create a file called meeting.txt"*
* *"Delete file old_draft.txt"* *(triggers safety confirmation preview card)*

### 📝 VoiceOS Dictation Mode
* Switch to Dictation Mode via system tray or say:
  - *"Dictate: Can you send me that form by tomorrow morning?"*
* Polished text is typed directly into your active cursor without verbal fillers.

### 👁️ Screen & Error Vision
* *"What is on my screen?"*
* *"Read this error"*
* *"What is this?"* *(analyzes the region directly around your mouse cursor)*

---

## 🧪 Running Automated Tests

Run the full pytest suite:
```powershell
python -m pytest tests/ -v
```
All 13 automated tests cover database persistence, turn linking, intent classification, browser routing, and safety guards.

---

## 📦 Building the Production Windows Installer (`JARVIS-Setup.exe`)

1. Build the standalone executable bundle with PyInstaller:
```powershell
pyinstaller installer/jarvis.spec
```
2. Compile the installer with Inno Setup:
```powershell
iscc installer/setup.iss
```
This outputs `dist/JARVIS-Setup.exe` which installs JARVIS as a native Windows desktop application with Start Menu and startup options, requiring zero Python or Git installations for the end user.
