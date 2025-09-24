"""
Google Drive service module for Meeting Minutes Generator
Handles OAuth authentication, file browsing, and file downloads
"""

import os
import pickle
import secrets
import tempfile
import webbrowser
from typing import Tuple, Optional, List, Dict, Any

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from config import (
    SCOPES, CREDENTIALS_FILE, TOKEN_FILE, GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET, OAUTH_REDIRECT_URI
)


class GoogleDriveService:
    """Service class for Google Drive operations"""

    def __init__(self):
        self.oauth_states = {}
        self.service = None

    def get_service(self) -> Tuple[Optional[Any], Optional[str]]:
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

    def start_oauth_flow(self) -> str:
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
            flow.redirect_uri = OAUTH_REDIRECT_URI

            # Generate a random state for security
            state = secrets.token_urlsafe(32)

            auth_url, _ = flow.authorization_url(
                prompt="consent", access_type="offline", state=state
            )

            # Store the state for later use
            self.oauth_states[state] = True

            # Open browser automatically
            webbrowser.open(auth_url)

            return f"🔗 Authorization opened in your browser!\n\nComplete the authorization and you'll be automatically redirected back to the app.\n\n⚠️ If you get an 'access_denied' error:\n1. Go to Google Cloud Console → OAuth consent screen\n2. Add your email to 'Test users' section\n3. Or publish the app to make it available to all users"

        except Exception as e:
            return f"❌ Error starting authorization: {str(e)}"

    def reset_oauth(self) -> str:
        """
        Reset OAuth by clearing stored tokens
        """
        try:
            # Remove token file if it exists
            if os.path.exists(TOKEN_FILE):
                os.remove(TOKEN_FILE)

            # Clear OAuth states
            self.oauth_states.clear()

            return "✅ Google Drive authorization reset successfully! You can now re-authorize with a fresh token."
        except Exception as e:
            return f"❌ Error resetting authorization: {str(e)}"

    def check_initial_auth_status(self) -> str:
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

    def handle_oauth_callback(self, request) -> str:
        """
        Handle OAuth callback from Google
        """
        try:
            # Get query parameters from FastAPI request
            code = request.query_params.get("code")
            state = request.query_params.get("state")
            error = request.query_params.get("error")

            if error:
                return self._create_error_html(f"Authorization failed: {error}")

            if not code or not state:
                return self._create_error_html("Invalid authorization response: Missing authorization code or state parameter.")

            # Verify state
            if state not in self.oauth_states:
                return self._create_error_html("Invalid state: Authorization state mismatch. Please try again.")

            # Recreate the flow for token exchange
            flow = Flow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            flow.redirect_uri = OAUTH_REDIRECT_URI

            # Exchange code for credentials
            flow.fetch_token(code=code)
            creds = flow.credentials

            # Save credentials
            with open(TOKEN_FILE, "wb") as token:
                pickle.dump(creds, token)

            # Clean up
            del self.oauth_states[state]

            return self._create_success_html()

        except Exception as e:
            return self._create_error_html(f"Authorization error: {str(e)}")

    def _create_error_html(self, error_message: str) -> str:
        """Create HTML error page"""
        return f"""
        <html>
            <head>
                <title>Authorization Failed</title>
            </head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px; background-color: #f5f5f5;">
                <div style="background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 500px; margin: 0 auto;">
                    <div style="font-size: 48px; color: #d32f2f; margin-bottom: 20px;">❌</div>
                    <h2 style="color: #d32f2f; margin-bottom: 20px;">Authorization Failed</h2>
                    <p style="color: #666; margin-bottom: 20px;">{error_message}</p>
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

    def _create_success_html(self) -> str:
        """Create HTML success page"""
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
                    setTimeout(() => {
                        try {
                            window.close();
                        } catch(e) {
                            window.location.href = '/';
                        }
                    }, 2000);
                    
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 3000);
                </script>
            </body>
        </html>
        """

    def get_file_path(self, service: Any, file_id: str, file_name: str) -> str:
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

    def browse_google_drive(self) -> Tuple[List[Tuple[str, str]], str]:
        """
        Browse and select files from Google Drive
        Returns tuple of (file_options, status_message)
        """
        try:
            # Get Google Drive service
            service, error = self.get_service()
            if service is None:
                return [], f"❌ {error}"

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
                    return [], "❌ No files found in your Google Drive."

            except Exception as e:
                return [], f"❌ Cannot access Google Drive files: {str(e)}"

            # Now search for audio files with multiple MIME type patterns
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
                return [], f"❌ No audio files found in your Google Drive. Found: {type_summary} files."

            # Create file options for dropdown selection
            file_options = []
            for file in all_audio_files[:20]:  # Limit to 20 files
                file_id = file["id"]
                file_name = file["name"]
                file_path = self.get_file_path(service, file_id, file_name)

                # Create a user-friendly option
                option_text = f"🎵 {file_name} - {file_path}"
                file_options.append((option_text, file_id))

            return file_options, f"✅ Found {len(all_audio_files)} audio files in your Google Drive."

        except Exception as e:
            return [], f"❌ Error browsing Google Drive: {str(e)}"

    def download_from_google_drive(self, file_input: str) -> Tuple[Optional[str], str]:
        """
        Download file from Google Drive using file ID or URL
        """
        try:
            # Get authenticated Google Drive service
            service, error = self.get_service()
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

    def check_google_drive_setup(self) -> Tuple[bool, str]:
        """
        Check if Google Drive API is properly configured
        """
        if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
            return (
                False,
                "Google OAuth credentials not found. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables.",
            )

        return True, "Google Drive OAuth configured successfully"
