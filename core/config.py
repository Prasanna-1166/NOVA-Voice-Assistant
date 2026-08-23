import os
from pathlib import Path

# Paths (Dynamic & Platform-Aware)
USER_HOME = Path.home()
DESKTOP_DIR = USER_HOME / "Desktop"
DOCUMENTS_DIR = USER_HOME / "Documents"
DOWNLOADS_DIR = USER_HOME / "Downloads"
PICTURES_DIR = USER_HOME / "Pictures"

# Ensure directories exist
for directory in [DESKTOP_DIR, DOCUMENTS_DIR, DOWNLOADS_DIR, PICTURES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Local Application Paths
LOCAL_APPDATA = USER_HOME / "AppData" / "Local"
OPENCODE_PATH = LOCAL_APPDATA / "Programs" / "opencode" / "OpenCode.exe"
VSCODE_PATH = LOCAL_APPDATA / "Programs" / "Microsoft VS Code" / "Code.exe"

# Model & Ollama Server Settings (Matches core/llm.py imports)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "qwen2.5:3b")
OLLAMA_REQUEST_TIMEOUT = 60  # seconds

# Voice & Assistant Settings
WAKE_WORD = "alexa"
ASSISTANT_NAME = "SWEETY"
DEFAULT_SYSTEM_PROMPT = (
    "You are SWEETY, an intelligent local AI assistant. "
    "Keep responses brief, polite, concise, and direct for speech output unless requested otherwise."
)