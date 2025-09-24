"""
Meeting Minutes Generator Package

A modular application for transcribing audio from meetings and generating 
professional meeting minutes using AI.
"""

__version__ = "1.0.0"
__author__ = "Meeting Minutes Generator Team"

from .app import MeetingMinutesApp
from .config import validate_config
from .google_drive_service import GoogleDriveService
from .audio_processor import AudioProcessor
from .ui_components import UIComponents

__all__ = [
    "MeetingMinutesApp",
    "validate_config",
    "GoogleDriveService",
    "AudioProcessor",
    "UIComponents"
]
