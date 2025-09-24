"""
Configuration module for Meeting Minutes Generator
Handles environment variables, constants, and configuration settings
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")

# Google Drive API Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.pickle"

# Model Configuration
AUDIO_MODEL = "whisper-1"
LLAMA_MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct"

# Application Configuration
APP_HOST = "0.0.0.0"
APP_PORT = 7860
OAUTH_REDIRECT_URI = f"http://localhost:{APP_PORT}/oauth/callback"

# File Configuration
SUPPORTED_AUDIO_FORMATS = ['.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg', '.wma']
MAX_FILE_SIZE_MB = 25

# UI Configuration
THEME = "soft"
APP_TITLE = "Meeting Minutes Generator"

def validate_config():
    """
    Validate that all required configuration is present
    """
    missing_configs = []

    if not OPENAI_API_KEY:
        missing_configs.append("OPENAI_API_KEY")

    if not GOOGLE_CLIENT_ID:
        missing_configs.append("GOOGLE_CLIENT_ID")

    if not GOOGLE_CLIENT_SECRET:
        missing_configs.append("GOOGLE_CLIENT_SECRET")

    if missing_configs:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_configs)}")

    return True
