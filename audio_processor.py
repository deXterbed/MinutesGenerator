"""
Audio processing module for Meeting Minutes Generator
Handles audio transcription and meeting minutes generation
"""

import os
from typing import Generator, Tuple, Optional
from openai import OpenAI

from config import OPENAI_API_KEY, AUDIO_MODEL


class AudioProcessor:
    """Service class for audio processing operations"""

    def __init__(self):
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY)

    def process_meeting_audio(
        self,
        audio_file: Optional[str],
        gdrive_file_id: Optional[str],
        download_callback,
        progress_callback=None
    ) -> Generator[Tuple[str, str], None, None]:
        """
        Process uploaded audio file and generate meeting minutes
        
        Args:
            audio_file: Path to local audio file
            gdrive_file_id: Google Drive file ID
            download_callback: Function to download from Google Drive
            progress_callback: Optional progress callback function
        
        Yields:
            Tuple of (transcription_status, meeting_minutes)
        """
        # Initial state: show initial status in transcription component
        yield "⏳ Initializing...", ""

        try:
            # Determine which file to use
            if gdrive_file_id:
                # Download from Google Drive
                yield "📁 Downloading from Google Drive...", ""
                audio_file_path, error = download_callback(gdrive_file_id)
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

            if progress_callback:
                progress_callback(0.1, desc="📁 File loaded successfully")
            yield "📁 File loaded successfully", ""

            if progress_callback:
                progress_callback(0.2, desc="🎙️ Starting audio transcription...")
            yield "🎙️ Starting audio transcription...", ""

            # Open the audio file in binary mode
            with open(audio_file_path, "rb") as audio_file_obj:
                if progress_callback:
                    progress_callback(0.3, desc="🔄 Transcribing audio (this may take a few minutes)...")
                yield "🔄 Transcribing audio (this may take a few minutes)...", ""

                # Transcribe the audio
                transcription = self.openai_client.audio.transcriptions.create(
                    model=AUDIO_MODEL, file=audio_file_obj, response_format="text"
                )

            if progress_callback:
                progress_callback(0.7, desc="✅ Transcription completed!")
            yield transcription, ""

            if progress_callback:
                progress_callback(0.8, desc="🤖 Generating meeting minutes...")
            yield transcription + "\n\n🤖 Generating meeting minutes...", ""

            # Generate meeting minutes
            meeting_minutes = self._generate_meeting_minutes(transcription)

            if progress_callback:
                progress_callback(0.95, desc="📝 Finalizing meeting minutes...")
            yield transcription + "\n\n📝 Finalizing meeting minutes...", meeting_minutes

            if progress_callback:
                progress_callback(1.0, desc="🎉 Complete! Meeting minutes generated successfully.")
            yield transcription, meeting_minutes

        except Exception as e:
            yield f"❌ Error: {str(e)}", ""

    def _generate_meeting_minutes(self, transcription: str) -> str:
        """
        Generate professional meeting minutes from transcription
        
        Args:
            transcription: Raw audio transcription text
            
        Returns:
            Formatted meeting minutes in markdown
        """
        # Create system message and user prompt
        system_message = (
            "You are an assistant that produces professional meeting minutes from audio transcripts. "
            "Create comprehensive minutes in markdown format with clear structure and actionable insights."
        )

        user_prompt = f"""Below is a transcript from a recorded meeting. Please analyze the transcript and create professional meeting minutes in markdown format. Include:

1. **Meeting Summary** - Overview of the meeting purpose and key outcomes
2. **Attendees** - List of participants (extract names mentioned)
3. **Key Discussion Points** - Main topics and decisions discussed
4. **Action Items** - Specific tasks with owners and deadlines (if mentioned)
5. **Next Steps** - Follow-up actions or future meetings
6. **Additional Notes** - Any other important information

Transcript:
{transcription}"""

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt},
        ]

        # Generate meeting minutes using OpenAI
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=2000,
            temperature=0.7
        )

        return response.choices[0].message.content

    def validate_audio_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate audio file format and size
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return False, "File does not exist"

            # Check file size (OpenAI Whisper limit is 25MB)
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)

            if file_size_mb > 25:
                return False, f"File size ({file_size_mb:.1f}MB) exceeds the 25MB limit"

            # Check file extension
            file_extension = os.path.splitext(file_path)[1].lower()
            supported_extensions = ['.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg', '.wma']

            if file_extension not in supported_extensions:
                return False, f"Unsupported file format: {file_extension}. Supported formats: {', '.join(supported_extensions)}"

            return True, "File is valid"

        except Exception as e:
            return False, f"Error validating file: {str(e)}"
