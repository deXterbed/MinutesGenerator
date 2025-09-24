"""
Server module for Meeting Minutes Generator
Provides a uvicorn-compatible app instance for development with reload
"""

from app import MeetingMinutesApp

# Create the app instance
app_instance = MeetingMinutesApp()
app = app_instance.create_app()

if __name__ == "__main__":
    app_instance.run(reload=False)
