"""
Meeting Minutes Generator

This script transcribes audio from recorded meetings and generates professional meeting minutes.
Works with any type of meeting audio file (MP3, WAV, etc.).

Usage:
1. Update AUDIO_FILE_PATH with your meeting audio file
2. Ensure you have OPENAI_API_KEY in your .env file
3. Run the script to get transcribed meeting minutes

Features:
- Audio transcription using OpenAI Whisper
- Professional meeting minutes generation using GPT-4
- Supports various meeting types (business, council, team meetings, etc.)
"""

import os
import requests
from openai import OpenAI
from huggingface_hub import login
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TextStreamer,
    pipeline,
    AutoProcessor,
    AutoModelForSpeechSeq2Seq,
)
import torch
from dotenv import load_dotenv
import gradio as gr
import tempfile
import urllib.parse
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import secrets
import webbrowser
from urllib.parse import urlparse, parse_qs

AUDIO_MODEL = "whisper-1"
LLAMA = "meta-llama/Meta-Llama-3.1-8B-Instruct"

load_dotenv(override=True)
hf_token = os.getenv("HF_TOKEN")
login(hf_token, add_to_git_credential=True)

openai_api_key = os.getenv("OPENAI_API_KEY")
openai = OpenAI(api_key=openai_api_key)

# Google Drive API configuration
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.pickle"

# OAuth configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")


def get_google_drive_service():
    """
    Get authenticated Google Drive service using OAuth
    """
    creds = None

    # Load existing token
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)

    # If no valid credentials, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                return None, f"Error refreshing credentials: {str(e)}"
        else:
            return None, "Please authorize Google Drive access first"

        # Save credentials for next run
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)

    try:
        service = build("drive", "v3", credentials=creds)
        return service, None
    except Exception as e:
        return None, f"Error creating Google Drive service: {str(e)}"


def start_oauth_flow():
    """
    Start OAuth flow for Google Drive with automatic redirect
    """
    try:
        if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
            return "❌ Google OAuth credentials not found. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables."

        # Check if already authorized
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, "rb") as token:
                creds = pickle.load(token)
            if creds and creds.valid:
                return "✅ Google Drive already authorized and ready to use!"

        # Use OAuth flow with automatic redirect
        flow = Flow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        flow.redirect_uri = "http://localhost:7860/oauth/callback"

        # Generate a random state for security
        state = secrets.token_urlsafe(32)

        auth_url, _ = flow.authorization_url(
            prompt="consent", access_type="offline", state=state
        )

        # Store the state for later use (we'll recreate the flow in callback)
        global oauth_states
        oauth_states[state] = True  # Just store a flag that this state is valid

        # Open browser automatically
        webbrowser.open(auth_url)

        return f"🔗 Authorization opened in your browser!\n\nComplete the authorization and you'll be automatically redirected back to the app.\n\n⚠️ If you get an 'access_denied' error:\n1. Go to Google Cloud Console → OAuth consent screen\n2. Add your email to 'Test users' section\n3. Or publish the app to make it available to all users"

    except Exception as e:
        return f"❌ Error starting authorization: {str(e)}"


def reset_oauth():
    """
    Reset OAuth by clearing stored tokens
    """
    try:
        # Remove token file if it exists
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)

        # Clear OAuth states
        global oauth_states
        oauth_states.clear()

        return "✅ Google Drive authorization reset successfully! You can now re-authorize with a fresh token."
    except Exception as e:
        return f"❌ Error resetting authorization: {str(e)}"


def check_initial_auth_status():
    """
    Check if user is already authorized when app loads
    """
    try:
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, "rb") as token:
                creds = pickle.load(token)
            if creds and creds.valid:
                return "✅ Google Drive already authorized and ready to use!"
        return "🔐 Google Drive not authorized. Click 'Authorize Google Drive' to get started."
    except Exception as e:
        return f"❌ Error checking authorization status: {str(e)}"


def handle_oauth_callback(request):
    """
    Handle OAuth callback from Google
    """
    try:
        # Get query parameters from FastAPI request
        code = request.query_params.get("code")
        state = request.query_params.get("state")
        error = request.query_params.get("error")

        if error:
            return f"""
            <html>
                <head>
                    <title>Authorization Failed</title>
                </head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px; background-color: #f5f5f5;">
                    <div style="background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 500px; margin: 0 auto;">
                        <div style="font-size: 48px; color: #d32f2f; margin-bottom: 20px;">❌</div>
                        <h2 style="color: #d32f2f; margin-bottom: 20px;">Authorization Failed</h2>
                        <p style="color: #666; margin-bottom: 20px;">Error: {error}</p>
                        <p style="color: #666; margin-bottom: 30px;">Please try again or contact support if the issue persists.</p>
                        <div style="margin: 20px 0;">
                            <a href="/" style="background: #1976d2; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">Return to App</a>
                        </div>
                    </div>
                    <script>
                        setTimeout(() => {{
                            try {{
                                window.close();
                            }} catch(e) {{
                                window.location.href = '/';
                            }}
                        }}, 3000);
                    </script>
                </body>
            </html>
            """

        if not code or not state:
            return """
            <html>
                <head>
                    <title>Invalid Authorization Response</title>
                </head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px; background-color: #f5f5f5;">
                    <div style="background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 500px; margin: 0 auto;">
                        <div style="font-size: 48px; color: #d32f2f; margin-bottom: 20px;">❌</div>
                        <h2 style="color: #d32f2f; margin-bottom: 20px;">Invalid Authorization Response</h2>
                        <p style="color: #666; margin-bottom: 30px;">Missing authorization code or state parameter.</p>
                        <div style="margin: 20px 0;">
                            <a href="/" style="background: #1976d2; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">Return to App</a>
                        </div>
                    </div>
                    <script>
                        setTimeout(() => {
                            try {
                                window.close();
                            } catch(e) {
                                window.location.href = '/';
                            }
                        }, 3000);
                    </script>
                </body>
            </html>
            """

        # Verify state
        if state not in oauth_states:
            return """
            <html>
                <head>
                    <title>Invalid State</title>
                </head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px; background-color: #f5f5f5;">
                    <div style="background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 500px; margin: 0 auto;">
                        <div style="font-size: 48px; color: #d32f2f; margin-bottom: 20px;">❌</div>
                        <h2 style="color: #d32f2f; margin-bottom: 20px;">Invalid State</h2>
                        <p style="color: #666; margin-bottom: 30px;">Authorization state mismatch. Please try again.</p>
                        <div style="margin: 20px 0;">
                            <a href="/" style="background: #1976d2; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">Return to App</a>
                        </div>
                    </div>
                    <script>
                        setTimeout(() => {
                            try {
                                window.close();
                            } catch(e) {
                                window.location.href = '/';
                            }
                        }, 3000);
                    </script>
                </body>
            </html>
            """

        # Recreate the flow for token exchange
        flow = Flow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        flow.redirect_uri = "http://localhost:7860/oauth/callback"

        # Exchange code for credentials
        flow.fetch_token(code=code)
        creds = flow.credentials

        # Save credentials
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)

        # Clean up
        del oauth_states[state]

        return """
        <html>
            <head>
                <title>Authorization Successful</title>
            </head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px; background-color: #f5f5f5;">
                <div style="background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 500px; margin: 0 auto;">
                    <div style="font-size: 48px; color: #2e7d32; margin-bottom: 20px;">✅</div>
                    <h2 style="color: #2e7d32; margin-bottom: 20px;">Authorization Successful!</h2>
                    <p style="color: #666; margin-bottom: 30px;">Google Drive access has been granted successfully.</p>
                    <p style="color: #666; margin-bottom: 30px;">Redirecting you back to the app...</p>
                    <div style="margin: 20px 0;">
                        <a href="/" style="background: #1976d2; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">Return to App</a>
                    </div>
                </div>
                <script>
                    // Try to close the window first (works if opened by the app)
                    setTimeout(() => {
                        try {
                            window.close();
                        } catch(e) {
                            // If window.close() fails, redirect to the main app
                            window.location.href = '/';
                        }
                    }, 2000);
                    
                    // Fallback redirect after 3 seconds
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 3000);
                </script>
            </body>
        </html>
        """

    except Exception as e:
        return f"""
        <html>
            <head>
                <title>Authorization Error</title>
            </head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px; background-color: #f5f5f5;">
                <div style="background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 500px; margin: 0 auto;">
                    <div style="font-size: 48px; color: #d32f2f; margin-bottom: 20px;">❌</div>
                    <h2 style="color: #d32f2f; margin-bottom: 20px;">Authorization Error</h2>
                    <p style="color: #666; margin-bottom: 20px;">Error: {str(e)}</p>
                    <p style="color: #666; margin-bottom: 30px;">Please try again or contact support if the issue persists.</p>
                    <div style="margin: 20px 0;">
                        <a href="/" style="background: #1976d2; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">Return to App</a>
                    </div>
                </div>
                <script>
                    setTimeout(() => {{
                        try {{
                            window.close();
                        }} catch(e) {{
                            window.location.href = '/';
                        }}
                    }}, 3000);
                </script>
            </body>
        </html>
        """


def check_google_drive_setup():
    """
    Check if Google Drive API is properly configured
    """
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return (
            False,
            "Google OAuth credentials not found. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables.",
        )

    return True, "Google Drive OAuth configured successfully"


def update_process_button_state(audio_file, gdrive_file):
    """
    Enable/disable the process button based on file selection
    """
    has_file = audio_file is not None or gdrive_file is not None
    return gr.update(interactive=has_file)


def update_dropdown_visibility(choices):
    """
    Update dropdown visibility and choices
    """
    if choices and len(choices) > 0:
        return gr.update(visible=True, choices=choices)
    else:
        return gr.update(visible=False, choices=[])


# Global variables for OAuth flow
current_flow = None
oauth_states = {}


def get_file_path(service, file_id, file_name):
    """
    Get the full path of a file in Google Drive
    """
    try:
        path_parts = [file_name]
        current_id = file_id

        while True:
            # Get file metadata
            file_metadata = (
                service.files().get(fileId=current_id, fields="parents").execute()
            )
            parents = file_metadata.get("parents", [])

            if not parents:
                break

            parent_id = parents[0]
            if parent_id == "0":  # Root folder
                break

            # Get parent folder name
            parent_metadata = (
                service.files().get(fileId=parent_id, fields="name").execute()
            )
            parent_name = parent_metadata.get("name", "Unknown")
            path_parts.insert(0, parent_name)
            current_id = parent_id

        return " / ".join(path_parts)
    except:
        return file_name  # Fallback to just filename if path resolution fails


def browse_google_drive():
    """
    Browse and select files from Google Drive
    """
    try:
        # Get Google Drive service
        service, error = get_google_drive_service()
        if service is None:
            return gr.update(choices=[], visible=False), f"❌ {error}"

        # First, let's check if we can access any files at all
        try:
            # List all recent files to test access
            all_files_query = "trashed=false"
            all_results = (
                service.files()
                .list(q=all_files_query, pageSize=5, fields="files(id, name, mimeType)")
                .execute()
            )
            all_files = all_results.get("files", [])

            if not all_files:
                return (
                    gr.update(choices=[], visible=False),
                    "❌ No files found in your Google Drive.",
                )

        except Exception as e:
            return (
                gr.update(choices=[], visible=False),
                f"❌ Cannot access Google Drive files: {str(e)}",
            )

        # Now search for audio files with multiple MIME type patterns
        # Note: Google Drive API searches recursively by default, so nested folders are included
        audio_queries = [
            "mimeType contains 'audio/' and trashed=false",
            "name contains '.mp3' and trashed=false",
            "name contains '.wav' and trashed=false",
            "name contains '.m4a' and trashed=false",
            "name contains '.flac' and trashed=false",
            "name contains '.aac' and trashed=false",
            "name contains '.ogg' and trashed=false",
            "name contains '.wma' and trashed=false",
        ]

        all_audio_files = []
        seen_ids = set()

        for query in audio_queries:
            try:
                results = (
                    service.files()
                    .list(
                        q=query,
                        pageSize=20,
                        fields="files(id, name, mimeType, webViewLink, parents)",
                    )
                    .execute()
                )
                files = results.get("files", [])

                for file in files:
                    if file["id"] not in seen_ids:
                        all_audio_files.append(file)
                        seen_ids.add(file["id"])

            except Exception as e:
                continue  # Skip this query if it fails

        if not all_audio_files:
            # Show what files we found instead
            file_types = {}
            for file in all_files[:10]:  # Check first 10 files
                mime_type = file.get("mimeType", "unknown")
                base_type = mime_type.split("/")[0] if "/" in mime_type else "unknown"
                file_types[base_type] = file_types.get(base_type, 0) + 1

            type_summary = ", ".join(
                [f"{count} {type}" for type, count in file_types.items()]
            )
            return (
                gr.update(choices=[], visible=False),
                f"❌ No audio files found in your Google Drive. Found: {type_summary} files.",
            )

        # Create file options for dropdown selection
        file_options = []
        for file in all_audio_files[:20]:  # Limit to 20 files
            file_id = file["id"]
            file_name = file["name"]
            file_mime = file.get("mimeType", "unknown")
            file_path = get_file_path(service, file_id, file_name)

            # Create a user-friendly option
            option_text = f"🎵 {file_name} - {file_path}"
            file_options.append((option_text, file_id))

        return (
            gr.update(choices=file_options, visible=True),
            f"✅ Found {len(all_audio_files)} audio files in your Google Drive.",
        )

    except Exception as e:
        return (
            gr.update(choices=[], visible=False),
            f"❌ Error browsing Google Drive: {str(e)}",
        )


def download_from_google_drive(file_input):
    """
    Download file from Google Drive using file ID or URL
    """
    try:
        # Get authenticated Google Drive service
        service, error = get_google_drive_service()
        if service is None:
            return None, error

        # Extract file ID from input (could be URL or direct ID)
        if "drive.google.com" in file_input:
            # Extract from URL
            if "/file/d/" in file_input:
                file_id = file_input.split("/file/d/")[1].split("/")[0]
            elif "id=" in file_input:
                file_id = file_input.split("id=")[1].split("&")[0]
            else:
                return None, "Invalid Google Drive URL format"
        else:
            # Assume it's a direct file ID
            file_id = file_input.strip()

        # Get file metadata
        try:
            file_metadata = service.files().get(fileId=file_id).execute()
            file_name = file_metadata.get("name", "downloaded_file")
        except Exception as e:
            return (
                None,
                f"Error accessing file: {str(e)}. Make sure you have access to this file.",
            )

        # Download the file content
        request = service.files().get_media(fileId=file_id)

        # Create temporary file with appropriate extension
        file_extension = os.path.splitext(file_name)[1] or ".mp3"
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)

        # Download and write content
        with open(temp_file.name, "wb") as f:
            downloader = request.execute()
            f.write(downloader)

        temp_file.close()

        return temp_file.name, f"File '{file_name}' downloaded successfully"

    except Exception as e:
        return None, f"Error downloading file: {str(e)}"


def process_meeting_audio(
    audio_file,
    gdrive_file_id,
    progress=gr.Progress(),
):
    """
    Process uploaded audio file and generate meeting minutes
    """
    # Initial state: show initial status in transcription component
    yield "⏳ Initializing...", ""

    try:
        import time
        import os

        # Determine which file to use
        if gdrive_file_id:
            # Download from Google Drive
            yield "📁 Downloading from Google Drive...", ""
            audio_file_path, error = download_from_google_drive(gdrive_file_id)
            if audio_file_path is None:
                yield f"❌ Error downloading from Google Drive: {error}", ""
                return
            yield "📁 Downloaded from Google Drive", ""
        elif audio_file:
            # Use local file
            audio_file_path = audio_file
            yield "📁 Using local file", ""
        else:
            yield "❌ Please upload an audio file or select one from Google Drive", ""
            return

        # Get file size for progress estimation
        file_size = os.path.getsize(audio_file_path)
        file_size_mb = file_size / (1024 * 1024)

        progress(0.1, desc="📁 File loaded successfully")
        yield "📁 File loaded successfully", ""  # Show status in transcription, clear minutes

        progress(0.2, desc="🎙️ Starting audio transcription...")
        yield "🎙️ Starting audio transcription...", ""  # Show status in transcription, clear minutes

        # Open the audio file in binary mode
        with open(audio_file_path, "rb") as audio_file_obj:
            progress(0.3, desc="🔄 Transcribing audio (this may take a few minutes)...")
            yield "🔄 Transcribing audio (this may take a few minutes)...", ""  # Show status in transcription, clear minutes

            # Transcribe the audio
            transcription = openai.audio.transcriptions.create(
                model=AUDIO_MODEL, file=audio_file_obj, response_format="text"
            )

        progress(0.7, desc="✅ Transcription completed!")
        yield transcription, ""  # Show actual transcription, clear minutes

        progress(0.8, desc="🤖 Generating meeting minutes...")
        yield transcription + "\n\n🤖 Generating meeting minutes...", ""  # Keep transcription + status, clear minutes

        # Create system message and user prompt
        system_message = "You are an assistant that produces professional meeting minutes from audio transcripts. Create comprehensive minutes in markdown format with clear structure and actionable insights."
        user_prompt = f"Below is a transcript from a recorded meeting. Please analyze the transcript and create professional meeting minutes in markdown format. Include:\n\n1. **Meeting Summary** - Overview of the meeting purpose and key outcomes\n2. **Attendees** - List of participants (extract names mentioned)\n3. **Key Discussion Points** - Main topics and decisions discussed\n4. **Action Items** - Specific tasks with owners and deadlines (if mentioned)\n5. **Next Steps** - Follow-up actions or future meetings\n6. **Additional Notes** - Any other important information\n\nTranscript:\n{transcription}"

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt},
        ]

        # Generate meeting minutes using OpenAI
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=2000,
            temperature=0.7
        )

        progress(0.95, desc="📝 Finalizing meeting minutes...")
        meeting_minutes = response.choices[0].message.content
        yield transcription + "\n\n📝 Finalizing meeting minutes...", meeting_minutes  # Keep transcription + status, show minutes

        progress(1.0, desc="🎉 Complete! Meeting minutes generated successfully.")
        yield transcription, meeting_minutes  # Final return: clean transcription, formatted minutes

    except Exception as e:
        yield f"❌ Error: {str(e)}", ""


# Create Gradio interface


def create_interface():
    with gr.Blocks(
        title="Meeting Minutes Generator", theme=gr.themes.Soft()
    ) as interface:
        gr.Markdown("""
        # 🎙️ Meeting Minutes Generator
        
        Upload an audio file from any meeting and get professional meeting minutes automatically generated!
        
        **Supported formats:** MP3, WAV, M4A, FLAC, and more
        """)

        with gr.Row():
            with gr.Column():
                # Audio file selection section
                gr.Markdown("### 📁 Select Audio File")

                # Local file upload
                audio_input = gr.Audio(
                    label="Upload Local Audio File", type="filepath", format="mp3"
                )

                # OR divider
                gr.Markdown("**OR**")

                # Google Drive section
                with gr.Group():
                    gr.Markdown("#### 🌐 Google Drive Integration")

                    # Google Drive authorization
                    with gr.Row():
                        auth_btn = gr.Button(
                            "🔐 Authorize Google Drive", variant="primary", scale=2
                        )
                        reset_btn = gr.Button(
                            "🔄 Reset Auth", variant="secondary", scale=1
                        )

                    # Google Drive setup status
                    gdrive_status = gr.Textbox(
                        label="Google Drive Status",
                        value=check_initial_auth_status(),
                        interactive=False,
                        lines=2,
                    )

                    # Google Drive file selection
                    browse_drive_btn = gr.Button(
                        "📁 Browse Google Drive Files",
                        variant="secondary",
                        visible=False,
                    )

                    gdrive_file_dropdown = gr.Dropdown(
                        label="Select Google Drive Audio File",
                        choices=[],
                        interactive=True,
                        visible=False,
                        info="Choose an audio file from your Google Drive",
                    )

                # Process button
                process_btn = gr.Button(
                    "Generate Meeting Minutes", variant="primary", interactive=False
                )

            with gr.Column():
                transcription_output = gr.Textbox(
                    label="Transcription",
                    lines=10,
                    max_lines=15,
                    placeholder="Transcribed text will appear here..."
                )

        meeting_minutes_output = gr.Markdown(
            value="Professional meeting minutes will appear here...",
            label="Meeting Minutes"
        )

        # Google Drive authorization button
        auth_btn.click(
            fn=start_oauth_flow, outputs=[gdrive_status], show_progress=False
        ).then(
            fn=lambda status: gr.update(
                visible="✅" in status and "already authorized" in status
            ),
            inputs=[gdrive_status],
            outputs=[browse_drive_btn],
        )

        # Reset authorization button
        reset_btn.click(fn=reset_oauth, outputs=[gdrive_status]).then(
            fn=lambda: gr.update(visible=False), outputs=[browse_drive_btn]
        ).then(
            fn=lambda: gr.update(visible=False, choices=[]),
            outputs=[gdrive_file_dropdown],
        )

        # Google Drive browse button click
        browse_drive_btn.click(
            fn=browse_google_drive, outputs=[gdrive_file_dropdown, gdrive_status]
        )

        # Initial check for authorization status to show browse button
        def check_initial_browse_visibility():
            try:
                if os.path.exists(TOKEN_FILE):
                    with open(TOKEN_FILE, "rb") as token:
                        creds = pickle.load(token)
                    if creds and creds.valid:
                        return gr.update(visible=True)
            except:
                pass
            return gr.update(visible=False)

        # Use the load event to check initial authorization status
        interface.load(fn=check_initial_browse_visibility, outputs=[browse_drive_btn])

        # Update process button state when files are selected
        audio_input.change(
            fn=update_process_button_state,
            inputs=[audio_input, gdrive_file_dropdown],
            outputs=[process_btn],
        )

        gdrive_file_dropdown.change(
            fn=update_process_button_state,
            inputs=[audio_input, gdrive_file_dropdown],
            outputs=[process_btn],
        )

        # Process button click
        process_btn.click(
            fn=process_meeting_audio,
            inputs=[audio_input, gdrive_file_dropdown],
            outputs=[transcription_output, meeting_minutes_output],
            show_progress=True,
        )

        # Example section
        gr.Markdown(
            """
        ## 📋 What You'll Get
        
        Professional meeting minutes with:
        - Meeting summary and key outcomes
        - List of attendees
        - Key discussion points and decisions
        - Action items with owners
        - Next steps and follow-ups
        - Additional important notes
        """
        )

    return interface

# Launch the interface
if __name__ == "__main__":
    import sys

    # Add --reload flag for development
    if "--reload" not in sys.argv:
        sys.argv.append("--reload")

    # Check if OAuth credentials are configured
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        print("❌ Google OAuth credentials not found!")
        print(
            "Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables."
        )
        print(
            "You can get these from Google Cloud Console → APIs & Services → Credentials"
        )
        sys.exit(1)

    # Create the interface
    interface = create_interface()

    # Create FastAPI app and mount Gradio interface
    from fastapi import FastAPI, Request
    from fastapi.responses import HTMLResponse

    app = FastAPI()

    # Add OAuth callback route to FastAPI app
    @app.get("/oauth/callback")
    def oauth_callback(request: Request):
        return HTMLResponse(handle_oauth_callback(request))

    # Mount Gradio interface onto FastAPI app
    app = gr.mount_gradio_app(app, interface, path="/")

    # Launch the FastAPI app
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7860)
