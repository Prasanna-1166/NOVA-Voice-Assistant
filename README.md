# 🎙️ NOVA (SWEETY)

### Privacy-First AI Desktop Assistant

> **NOVA** is an AI-powered desktop assistant built in Python that combines **local LLMs, voice interaction, task automation, document generation, reminders, and Windows system control** into a single productivity platform.

NOVA is designed with a **local-first architecture**, using Ollama for local LLM inference and Whisper for local speech recognition, reducing dependency on cloud AI APIs.

---

## ✨ Key Features

### 🧠 AI & Voice

* Local LLM integration using **Ollama + Qwen2.5**
* Local speech-to-text using **Whisper**
* Voice and text interaction
* Wake-word based activation
* Text-to-speech responses

### 📄 Productivity

* AI-generated Word documents (`.docx`)
* Formal letters, reports, notes, essays, and applications
* Background reminders and timers
* Local task management

### 💻 Desktop Automation

* Launch applications such as VS Code, Chrome, Word, OpenCode, Terminal, etc.
* Windows volume control and mute/unmute
* Screenshot capture
* YouTube/media automation
* WhatsApp desktop automation

### ⚡ Architecture

* Multi-threaded voice and text pipelines
* Non-blocking background tasks
* Modular tool-based architecture
* Designed for future RAG and multi-agent integration

---

## 🏗️ Architecture

```text
                    ┌───────────────┐
                    │     USER      │
                    └───────┬───────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
         🎙️ Voice Input              ⌨️ Text Input
              │                           │
           Whisper                    Terminal
              │                           │
              └─────────────┬─────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ NOVA Assistant│
                    │  + Local LLM  │
                    └───────┬───────┘
                            │
                     Tool Selection
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
      Documents          Tasks            System
      & Word             & Reminders      Automation
          │                 │                 │
          └─────────────────┼─────────────────┘
                            │
                            ▼
                       User Response
```

---

## 🛠️ Technology Stack

| Category       | Technology           |
| -------------- | -------------------- |
| Language       | Python               |
| LLM            | Ollama + Qwen2.5     |
| Speech-to-Text | OpenAI Whisper       |
| Text-to-Speech | Edge-TTS             |
| Audio          | pygame-ce            |
| Documents      | python-docx          |
| Windows Audio  | PyCAW                |
| Automation     | PyAutoGUI, pywhatkit |
| Screen Capture | mss                  |
| Concurrency    | Python threading     |
| Platform       | Windows 10/11        |

> **Note:** NOVA's core AI processing can run locally. Some integrations such as Edge-TTS, YouTube, and WhatsApp may require internet connectivity.

---

## 📂 Project Structure

```text
NOVA/
│
├── main.py
├── requirements.txt
├── README.md
│
├── core/
│   ├── assistant.py
│   ├── config.py
│   ├── llm.py
│   ├── task_manager.py
│   └── tools.py
│
└── voice/
    ├── stt.py
    ├── tts.py
    └── wakeword.py
```

---

## 💡 Example Commands

```text
"Create a formal leave letter and open it in Word."

"Remind me in 30 minutes to submit my assignment."

"Open VS Code."

"Launch OpenCode."

"Set volume to 50."

"Take a screenshot."

"Play lofi music on YouTube."
```

NOVA converts natural-language requests into actions through its AI and tool-execution layer.

---

## 🚀 Installation

### Requirements

* Windows 10/11
* Python 3.10+
* Ollama
* Microsoft Word
* Microphone

### Setup

```powershell
git clone https://github.com/Prasanna-1166/NOVA-Voice-Assistant.git
cd NOVA-Voice-Assistant

python -m venv venv
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt

ollama pull qwen2.5

python main.py
```

---

## 🛣️ Roadmap

### Current

* [x] Local LLM integration
* [x] Voice interaction
* [x] Speech-to-text
* [x] Text-to-speech
* [x] Document generation
* [x] Reminders and timers
* [x] Application automation
* [x] Windows system controls
* [x] Screenshot capture

### Planned

* [ ] Persistent personal memory
* [ ] RAG-based document knowledge
* [ ] Calendar and schedule management
* [ ] Advanced task management
* [ ] Coding agent
* [ ] Study/research agent
* [ ] Multi-agent orchestration
* [ ] Fully offline TTS
* [ ] Cross-platform support

---

## 🎯 Future Vision

NOVA is being developed toward a **personal AI operating layer** rather than a simple voice assistant.

The long-term architecture will combine:

```text
             NOVA
               │
       AI Orchestrator
               │
    ┌──────────┼──────────┐
    │          │          │
 Coding      Study    Productivity
 Agent       Agent       Agent
    │          │          │
    └──────────┼──────────┘
               │
        System Automation
```

This will allow NOVA to handle complex multi-step tasks such as **planning, coding, studying, document creation, scheduling, and computer automation** through a single interface.

---

## 🔐 Privacy

NOVA follows a **local-first approach**.

* LLM inference → Local Ollama
* Speech recognition → Local Whisper
* Documents → Generated locally
* Task processing → Local

Some optional integrations may require internet access.

---

## 👨‍💻 Author

### Prasanna Kumar

**B.Tech CSE | AI & Generative AI Enthusiast**

Interested in:

`Generative AI` · `LLMs` · `RAG` · `AI Agents` · `Machine Learning` · `Python` · `Automation`

---

## ⭐ Support

If you find NOVA interesting, consider giving the repository a ⭐.

**Repository:** `github.com/Prasanna-1166/NOVA-Voice-Assistant`

---

> **NOVA — From a voice assistant to a personal AI platform.**

If you want to develop it more , you can feel free to contact me , we can work together and develop it more.