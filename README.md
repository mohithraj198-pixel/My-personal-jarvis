# 🤖 J.A.R.V.I.S: Personal Voice-Controlled AI Assistant

> An intelligent, voice-activated desktop AI assistant developed by **Mohith** in Python. J.A.R.V.I.S listens, understands natural commands, thinks, speaks in real-time, and automates your computer tasks effortlessly.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Stars](https://img.shields.io/github/stars/mohithraj198-pixel/My-personal-jarvis?style=for-the-badge&color=yellow)](https://github.com/mohithraj198-pixel/My-personal-jarvis/stargazers)
[![Forks](https://img.shields.io/github/forks/mohithraj198-pixel/My-personal-jarvis?style=for-the-badge&color=blue)](https://github.com/mohithraj198-pixel/My-personal-jarvis/network/members)

![J.A.R.V.I.S in action](https://github.com/user-attachments/assets/59727c15-d85a-41bc-b27d-bea08b3b3a41)

---

## 🌟 Overview

**J.A.R.V.I.S (Just A Rather Very Intelligent System)** is a personal voice-controlled assistant built by **Mohith**, inspired by Iron Man's iconic AI. You speak naturally to it, and Jarvis understands the intent, executes system or web automation, and responds out loud with natural neural voice synthesis.

It is designed with modular, swappable subsystems for maximum performance, offline reliability, and fast response times.

---

## ✨ Features & Capabilities

| Subsystem | Description |
|---|---|
| 🎙️ **Speech Recognition** | Real-time speech-to-text input with continuous listening |
| 🗣️ **Neural Text-to-Speech** | Natural, human-like voice responses powered by neural TTS with offline fallback |
| 🧠 **Brain & Reasoning** | LLM-powered conversational understanding and contextual memory |
| 🌐 **Live Web Search** | Real-time web search for up-to-date news, information, and answers |
| 🎨 **Image Generation** | AI image generation right from spoken voice prompts |
| 👁️ **Computer Vision** | Camera capture and visual analysis |
| ⚙️ **System Automation** | App launching, volume control, brightness adjustments, and process monitoring |
| 💬 **WhatsApp Automation** | Send messages and open WhatsApp completely hands-free |
| ⛅ **Weather Updates** | Live real-time weather reports for any city |
| ⏰ **Time & Reminders** | Set alarms, reminders, and daily schedule management |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10** or newer
- A working microphone and speakers/headphones
- **Google Chrome** or **Microsoft Edge**

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mohithraj198-pixel/My-personal-jarvis.git
   cd My-personal-jarvis
   ```

2. **Create and activate a virtual environment (recommended):**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 🎯 How to Run

### Option 1: Desktop Animated UI (Recommended)
```bash
python ui.py
```

### Option 2: Terminal Mode
```bash
python jarvis.py
```

---

## 🗣️ Voice Commands & Usage

Simply say the wake word or speak naturally into your microphone:

- ⛅ *"What is the weather in Bangalore?"*
- 🌐 *"Open Microsoft Edge and search for quantum computing"*
- 🎨 *"Generate an image of a red sports car at sunset"*
- 💬 *"Open WhatsApp"*
- 📰 *"What is happening in the news right now?"*
- ⏰ *"Set an alarm for 7:00 AM"*
- 🔊 *"Increase the volume to 80 percent"*

---

## 📁 Project Structure

```
My-personal-jarvis/
├── jarvis.py              # Main entry point & intent routing
├── ui.py                  # PyQt5 animated desktop interface
├── co_brain.py            # Assistant reasoning & decision hub
├── NetHyTechSTT/          # Speech-to-text engine
├── TextToSpeech/          # Neural voice output engine
├── Brain/                 # Conversational AI brain & memory
├── Automation/            # Desktop, app, and system control
├── Real_Time/             # Live web intelligence
├── Vision/                # Camera & visual recognition
├── TextToImage/           # Image generation module
├── Whatsapp_automation/   # Messaging & chat automation
├── Weather_Check/         # Real-time weather service
└── Time_Operations/       # Alarms, timers, and scheduling
```

---

## 🛠️ Tech Stack

- **Core:** Python 3.10+
- **GUI:** PyQt5
- **Speech & Audio:** Edge-TTS, Pygame, PyAudio
- **Web & Automation:** Selenium, PyAutoGUI, PyWhatKit, Requests
- **Vision:** OpenCV

---

## 👤 Author

Developed with ❤️ by **Mohith**

- **GitHub:** [@mohithraj198-pixel](https://github.com/mohithraj198-pixel)
- **Repository:** [My-personal-jarvis](https://github.com/mohithraj198-pixel/My-personal-jarvis)

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
