"""
UI components module for Meeting Minutes Generator
Handles Gradio interface creation and component management
"""

import os
import pickle
import gradio as gr
from typing import Optional, Tuple, List

from config import THEME, APP_TITLE, TOKEN_FILE
from google_drive_service import GoogleDriveService
from audio_processor import AudioProcessor


class UIComponents:
    """Class for managing UI components and interactions"""

    def __init__(self, google_drive_service: GoogleDriveService, audio_processor: AudioProcessor):
        self.google_drive_service = google_drive_service
        self.audio_processor = audio_processor

    def create_interface(self) -> gr.Blocks:
        """
        Create the main Gradio interface
        """
        with gr.Blocks(title=APP_TITLE, theme=gr.themes.Soft()) as interface:
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
                            value=self.google_drive_service.check_initial_auth_status(),
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

            # Set up event handlers
            self._setup_event_handlers(
                interface, auth_btn, reset_btn, browse_drive_btn, gdrive_file_dropdown,
                audio_input, process_btn, transcription_output, meeting_minutes_output,
                gdrive_status
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

    def _setup_event_handlers(
        self, interface, auth_btn, reset_btn, browse_drive_btn, gdrive_file_dropdown,
        audio_input, process_btn, transcription_output, meeting_minutes_output, gdrive_status
    ):
        """Set up all event handlers for the interface"""

        # Google Drive authorization button
        auth_btn.click(
            fn=self.google_drive_service.start_oauth_flow,
            outputs=[gdrive_status],
            show_progress=False
        ).then(
            fn=lambda status: gr.update(
                visible="✅" in status and "already authorized" in status
            ),
            inputs=[gdrive_status],
            outputs=[browse_drive_btn],
        )

        # Reset authorization button
        reset_btn.click(fn=self.google_drive_service.reset_oauth, outputs=[gdrive_status]).then(
            fn=lambda: gr.update(visible=False), outputs=[browse_drive_btn]
        ).then(
            fn=lambda: gr.update(visible=False, choices=[]),
            outputs=[gdrive_file_dropdown],
        )

        # Google Drive browse button click
        browse_drive_btn.click(
            fn=self._browse_google_drive_wrapper,
            outputs=[gdrive_file_dropdown, gdrive_status]
        )

        # Initial check for authorization status to show browse button
        interface.load(fn=self._check_initial_browse_visibility, outputs=[browse_drive_btn])

        # Update process button state when files are selected
        audio_input.change(
            fn=self._update_process_button_state,
            inputs=[audio_input, gdrive_file_dropdown],
            outputs=[process_btn],
        )

        gdrive_file_dropdown.change(
            fn=self._update_process_button_state,
            inputs=[audio_input, gdrive_file_dropdown],
            outputs=[process_btn],
        )

        # Process button click
        process_btn.click(
            fn=self._process_meeting_audio_wrapper,
            inputs=[audio_input, gdrive_file_dropdown],
            outputs=[transcription_output, meeting_minutes_output],
            show_progress=True,
        )

    def _browse_google_drive_wrapper(self) -> Tuple[gr.Dropdown, str]:
        """
        Wrapper for browse_google_drive to handle Gradio dropdown updates
        """
        file_options, status_message = self.google_drive_service.browse_google_drive()

        if file_options and len(file_options) > 0:
            return gr.update(choices=file_options, visible=True), status_message
        else:
            return gr.update(choices=[], visible=False), status_message

    def _check_initial_browse_visibility(self) -> gr.Button:
        """
        Check initial authorization status to show browse button
        """
        try:
            if os.path.exists(TOKEN_FILE):
                with open(TOKEN_FILE, "rb") as token:
                    creds = pickle.load(token)
                if creds and creds.valid:
                    return gr.update(visible=True)
        except:
            pass
        return gr.update(visible=False)

    def _update_process_button_state(self, audio_file: Optional[str], gdrive_file: Optional[str]) -> gr.Button:
        """
        Enable/disable the process button based on file selection
        """
        has_file = audio_file is not None or gdrive_file is not None
        return gr.update(interactive=has_file)

    def _process_meeting_audio_wrapper(
        self, audio_file: Optional[str], gdrive_file_id: Optional[str], progress=gr.Progress()
    ) -> Tuple[str, str]:
        """
        Wrapper for process_meeting_audio to handle Gradio progress and outputs
        """
        def progress_callback(progress_value: float, desc: str):
            progress(progress_value, desc=desc)

        def download_callback(file_id: str):
            return self.google_drive_service.download_from_google_drive(file_id)

        # Get the generator from audio processor
        result_generator = self.audio_processor.process_meeting_audio(
            audio_file=audio_file,
            gdrive_file_id=gdrive_file_id,
            download_callback=download_callback,
            progress_callback=progress_callback
        )

        # Get the final result (last yielded value)
        final_transcription = ""
        final_minutes = ""

        for transcription, minutes in result_generator:
            final_transcription = transcription
            final_minutes = minutes

        return final_transcription, final_minutes
