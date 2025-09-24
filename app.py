"""
Main application module for Meeting Minutes Generator
Coordinates all services and handles application startup
"""

import sys
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import gradio as gr

from config import (
    validate_config, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET,
    APP_HOST, APP_PORT, OAUTH_REDIRECT_URI
)
from google_drive_service import GoogleDriveService
from audio_processor import AudioProcessor
from ui_components import UIComponents


class MeetingMinutesApp:
    """Main application class"""

    def __init__(self):
        self.google_drive_service = GoogleDriveService()
        self.audio_processor = AudioProcessor()
        self.ui_components = UIComponents(self.google_drive_service, self.audio_processor)
        self.app = None
        self.interface = None

    def create_app(self) -> FastAPI:
        """
        Create and configure the FastAPI application
        """
        # Validate configuration
        try:
            validate_config()
        except ValueError as e:
            print(f"❌ Configuration Error: {e}")
            print("Please set the required environment variables and try again.")
            sys.exit(1)

        # Create FastAPI app
        self.app = FastAPI(title="Meeting Minutes Generator")

        # Add OAuth callback route
        @self.app.get("/oauth/callback")
        def oauth_callback(request: Request):
            return HTMLResponse(self.google_drive_service.handle_oauth_callback(request))

        # Create Gradio interface
        self.interface = self.ui_components.create_interface()

        # Mount Gradio interface onto FastAPI app
        self.app = gr.mount_gradio_app(self.app, self.interface, path="/")

        return self.app

    def run(self, reload: bool = False):
        """
        Run the application
        """
        if self.app is None:
            self.create_app()

        print(f"🚀 Starting Meeting Minutes Generator on {APP_HOST}:{APP_PORT}")
        print(f"📱 Access the application at: http://localhost:{APP_PORT}")
        print(f"🔐 OAuth callback URL: {OAUTH_REDIRECT_URI}")

        uvicorn.run(
            self.app,
            host=APP_HOST,
            port=APP_PORT,
            reload=reload
        )


def main():
    """
    Main entry point for the application
    """
    # Check if OAuth credentials are configured
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        print("❌ Google OAuth credentials not found!")
        print("Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables.")
        print("You can get these from Google Cloud Console → APIs & Services → Credentials")
        sys.exit(1)

    # Check for --reload flag for development
    reload_mode = "--reload" in sys.argv

    # Create and run the application
    app = MeetingMinutesApp()
    app.run(reload=reload_mode)


if __name__ == "__main__":
    main()
