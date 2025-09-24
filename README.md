# 🎙️ Meeting Minutes Generator

A powerful, modular web application that automatically transcribes audio from meetings and generates professional meeting minutes using AI. Built with a clean architecture for easy maintenance and extensibility.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![OpenAI](https://img.shields.io/badge/OpenAI-Whisper%20%2B%20GPT--4-green.svg)](https://openai.com)
[![Gradio](https://img.shields.io/badge/Gradio-Web%20Interface-orange.svg)](https://gradio.app)
[![Google Drive](https://img.shields.io/badge/Google%20Drive-API%20Integration-red.svg)](https://developers.google.com/drive)

## ✨ Features

- **🎤 High-Quality Transcription**: Uses OpenAI Whisper for accurate speech-to-text conversion
- **🤖 AI-Powered Analysis**: Generates structured meeting minutes with GPT-4
- **📁 Multiple Input Sources**: Upload local files or browse Google Drive files
- **📋 Professional Output**: Creates formatted minutes with summaries, action items, and key points
- **🌐 Modern Web Interface**: User-friendly Gradio interface with real-time progress
- **🔐 Secure Authentication**: OAuth2 integration with Google Drive
- **🏗️ Modular Architecture**: Clean, maintainable codebase with separation of concerns

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** - [Download Python](https://python.org/downloads/)
- **OpenAI API Key** - [Get your API key](https://platform.openai.com/api-keys)
- **Google Cloud Account** - [Sign up for Google Cloud](https://cloud.google.com/) (optional, for Google Drive integration)
- **Audio Files** - Meeting recordings in supported formats (MP3, WAV, M4A, FLAC, AAC, OGG, WMA)

### 📦 Installation

1. **Clone or download this repository**
   ```bash
   git clone https://github.com/deXterbed/MinutesGenerator
   cd MinutesGenerator
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**

   Create a `.env` file in the project directory:
   ```env
   # Required - Get from https://platform.openai.com/api-keys
   OPENAI_API_KEY=your_openai_api_key_here

   # Required for Google Drive integration
   GOOGLE_CLIENT_ID=your_google_client_id_here
   GOOGLE_CLIENT_SECRET=your_google_client_secret_here

   # Optional - For Hugging Face models (not currently used)
   HF_TOKEN=your_huggingface_token_here
   ```

### 🏃‍♂️ Running the Application

**Option 1 - Simple run (recommended for first-time users):**
```bash
python run.py
```

**Option 2 - Direct app run:**
```bash
python app.py
```

**Option 3 - Development with auto-reload (for developers):**
```bash
uvicorn server:app --reload --host 0.0.0.0 --port 7860
```

### 🌐 Access the Application

Once running, open your browser and navigate to:
**http://localhost:7860**

> 💡 **Tip**: The application will automatically open your default browser when started.

## 🔗 Google Drive Integration Setup

> ⚠️ **Note**: Google Drive integration is optional. You can use the app with local file uploads only.

### 📋 Prerequisites

- Google Cloud account
- Google Drive with audio files
- Basic understanding of OAuth2

### 🛠️ Step-by-Step Setup

#### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your project ID for reference

#### Step 2: Enable Google Drive API

1. In the Google Cloud Console, navigate to **"APIs & Services"** → **"Library"**
2. Search for **"Google Drive API"**
3. Click on it and press **"Enable"**

#### Step 3: Configure OAuth Consent Screen

1. Go to **"APIs & Services"** → **"OAuth consent screen"**
2. Choose **"External"** user type
3. Fill in the required information:
   - **App name**: Meeting Minutes Generator
   - **User support email**: Your email
   - **Developer contact information**: Your email
4. Add your email to **"Test users"** section
5. Upload the app logo (use `meeting_minutes_oauth_logo.png` from this project)
6. Add the following scope:
   - **Scope**: `https://www.googleapis.com/auth/drive.readonly`
   - **Description**: "Read access to Google Drive files"

#### Step 4: Create OAuth2 Credentials

1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"Create Credentials"** → **"OAuth client ID"**
3. For Application type, choose **"Web application"**
4. Give it a name (e.g., "Meeting Minutes Generator")
5. Add authorized redirect URIs:
   - `http://localhost:7860/oauth/callback`
6. Click **"Create"**
7. Copy the **Client ID** and **Client Secret**

#### Step 5: Update Environment Variables

Add your OAuth credentials to your `.env` file:
```env
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
```

#### Step 6: First-time Authorization

1. Run the application: `python run.py`
2. Click **"Authorize Google Drive"** in the interface
3. Complete the OAuth flow in your browser
4. Grant permissions to the application
5. You'll be redirected back to the app automatically

> 🔒 **Security Note**: The app requests read-only access to your Google Drive files to browse and access audio files.

## 📁 File Structure

```
MinutesGenerator/
├── app.py                              # Main application entry point
├── server.py                           # Uvicorn-compatible server for development
├── config.py                           # Configuration and environment variables
├── google_drive_service.py             # Google Drive OAuth and file operations
├── audio_processor.py                  # Audio transcription and minutes generation
├── ui_components.py                    # Gradio interface components
├── __init__.py                         # Package initialization
├── run.py                              # Simple entry point script
├── run_original.py                     # Original monolithic version (backup)
├── requirements.txt                    # Python dependencies
├── README.md                          # This file
├── .env                               # Environment variables (create this)
├── credentials.json                   # Google OAuth credentials (download this)
├── token.pickle                       # Saved OAuth token (auto-generated)
├── meeting_minutes_oauth_logo.png     # OAuth consent screen logo
└── meeting_minutes_oauth_logo.jpg     # OAuth consent screen logo (JPG)
```

## 🏗️ Architecture

The application is built with a modular architecture for better maintainability and separation of concerns:

### Core Modules

- **`app.py`** - Main application entry point and FastAPI server setup
- **`config.py`** - Configuration management, environment variables, and constants
- **`google_drive_service.py`** - Google Drive OAuth authentication and file operations
- **`audio_processor.py`** - Audio transcription and meeting minutes generation
- **`ui_components.py`** - Gradio interface components and event handlers

### Key Benefits

- **Separation of Concerns**: Each module has a single responsibility
- **Easy Testing**: Individual components can be tested in isolation
- **Maintainability**: Changes to one module don't affect others
- **Reusability**: Components can be reused in other projects
- **Scalability**: Easy to add new features or modify existing ones

## 🎯 How to Use

### 📁 Local File Upload

1. **Upload Audio File**
   - Click "Upload Local Audio File"
   - Select your meeting audio file (MP3, WAV, M4A, FLAC, etc.)
   - Supported formats: MP3, WAV, M4A, FLAC, AAC, OGG, WMA

2. **Generate Minutes**
   - Click "Generate Meeting Minutes"
   - Wait for processing to complete (usually 1-3 minutes)
   - View the transcription and formatted meeting minutes

### 🌐 Google Drive Integration

1. **Authorize Access** (first time only)
   - Click "Authorize Google Drive"
   - Complete the OAuth flow in your browser
   - Grant permissions to the application

2. **Browse Files**
   - Click "Browse Google Drive Files"
   - Select an audio file from the dropdown
   - The app will automatically download and process the file

3. **Generate Minutes**
   - Click "Generate Meeting Minutes"
   - Wait for processing to complete
   - View the results

### 📊 Processing Steps

The application follows these steps:
1. **File Validation** - Checks file format and size
2. **Audio Transcription** - Uses OpenAI Whisper for speech-to-text
3. **AI Analysis** - GPT-4 generates structured meeting minutes
4. **Output Generation** - Creates formatted markdown output

## 📋 Output Format

The generated meeting minutes include:

- **📝 Meeting Summary**: Overview and key outcomes
- **👥 Attendees**: List of participants (extracted from transcript)
- **💬 Key Discussion Points**: Main topics and decisions
- **✅ Action Items**: Specific tasks with owners and deadlines
- **🔄 Next Steps**: Follow-up actions and future meetings
- **📌 Additional Notes**: Other important information

### 📄 Example Output

```markdown
# Meeting Minutes - Project Planning Session

## Meeting Summary
Discussion focused on Q1 project roadmap, resource allocation, and timeline adjustments.

## Attendees
- John Smith (Project Manager)
- Sarah Johnson (Lead Developer)
- Mike Chen (Designer)

## Key Discussion Points
- Reviewed current project status
- Discussed budget constraints
- Agreed on new timeline

## Action Items
- [ ] John: Finalize budget proposal by Friday
- [ ] Sarah: Complete technical specifications by next week
- [ ] Mike: Update design mockups by Wednesday

## Next Steps
- Schedule follow-up meeting for next Friday
- Review progress on action items
- Update project timeline

## Additional Notes
- Consider hiring additional developer for Q2
- Budget approval pending from finance team
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with:

```env
# Required - OpenAI API key for transcription and minutes generation
OPENAI_API_KEY=your_openai_api_key_here

# Required - Google Drive OAuth credentials
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

# Optional - Hugging Face token (not currently used in the app)
HF_TOKEN=your_huggingface_token_here
```

### Google Drive Scopes

The app uses the following Google Drive scope:
- `https://www.googleapis.com/auth/drive.readonly` - Read-only access to Google Drive files

This provides read-only access to browse and download files from your Google Drive for processing.

## 🛠️ Troubleshooting

### 🚨 Common Issues

#### **"Google Drive API not configured"**
- ✅ Ensure `credentials.json` is in the correct location
- ✅ Check that Google Drive API is enabled in Google Cloud Console
- ✅ Verify your OAuth credentials are correct

#### **"First-time setup required"**
- ✅ Follow the authorization URL provided
- ✅ Complete the OAuth flow in your browser
- ✅ Make sure you're added as a test user in Google Cloud Console

#### **"Error accessing file"**
- ✅ Ensure you have access to the Google Drive file
- ✅ Check that the file URL is correct
- ✅ Verify the file is not restricted or in a private folder

#### **Audio processing errors**
- ✅ Check that your OpenAI API key is valid and has credits
- ✅ Ensure the audio file format is supported
- ✅ Verify the file is not corrupted
- ✅ Check file size (must be under 25MB)

#### **App exits automatically**
- ✅ Use `python run.py` instead of `python app.py`
- ✅ Check that all environment variables are set
- ✅ Ensure no other process is using port 7860

### 📏 File Size Limits

- **OpenAI Whisper**: Up to 25MB audio files
- **Google Drive**: Standard file size limits apply
- **OAuth Logo**: Must be under 1MB, 120x120px

### 🔍 Debug Mode

The app doesn't currently have a built-in debug mode, but you can:

1. **Check logs**: Look at the terminal output for error messages
2. **Validate environment**: Ensure all required environment variables are set
3. **Test components**: Run individual modules to isolate issues

## 🔒 Security & Privacy

- **🔐 Local Processing**: Audio files are processed locally and not stored permanently
- **🗑️ Temporary Files**: Google Drive files are downloaded temporarily and deleted after processing
- **🔑 OAuth Security**: Uses secure OAuth2 authentication with proper token management
- **🔒 API Keys**: Store securely in environment variables, never in code
- **👁️ Read-Only Access**: App only reads files, doesn't modify Google Drive content
- **🛡️ Data Privacy**: No audio data is stored or transmitted to third parties except OpenAI

## 🚀 Current Features

### ✅ Implemented Features

- **Audio Transcription**: OpenAI Whisper integration for speech-to-text
- **AI Minutes Generation**: GPT-4 powered meeting minutes creation
- **Local File Upload**: Support for MP3, WAV, M4A, FLAC, AAC, OGG, WMA
- **Google Drive Integration**: Browse and download files from Google Drive
- **OAuth2 Authentication**: Secure Google Drive access
- **Real-time Progress**: Live progress tracking during processing
- **Modular Architecture**: Clean, maintainable codebase

### 🔮 Future Enhancements

- **Model Selection**: Switch between different OpenAI models
- **Output Format**: Customize meeting minutes structure
- **Language Support**: Multi-language transcription support
- **Batch Processing**: Process multiple files at once
- **Caching**: Intelligent caching of processed files
- **Parallel Processing**: Multiple file processing support

## 📄 License

This project is for educational and personal use. Please ensure you comply with:
- [OpenAI's usage policies](https://openai.com/policies/usage-policies)
- [Google's API terms of service](https://developers.google.com/terms)

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **🐛 Report Issues**: Found a bug? Let us know!
2. **💡 Feature Requests**: Have an idea? We'd love to hear it!
3. **🔧 Code Contributions**: Submit pull requests for improvements
4. **📚 Documentation**: Help improve our documentation
5. **⭐ Star the Project**: Show your support!

### Development Setup

```bash
# Clone the repository
git clone https://github.com/deXterbed/MinutesGenerator
cd MinutesGenerator

# Install development dependencies
pip install -r requirements.txt

# Set up environment variables
# Create a .env file with your API keys (see Configuration section)

# Run in development mode
uvicorn server:app --reload --host 0.0.0.0 --port 7860
```

## 📞 Support

### Getting Help

1. **📖 Check Documentation**: Review this README thoroughly
2. **🔍 Troubleshooting**: Check the troubleshooting section above
3. **🌐 Google Cloud Setup**: Verify your Google Cloud Console configuration
4. **🔑 API Keys**: Ensure your API keys and credentials are correct
5. **📝 Logs**: Check the application logs for detailed error messages

### Community

- **💬 Discussions**: Join our community discussions
- **📧 Contact**: Reach out for support
- **🐛 Issues**: Report bugs and issues
- **💡 Ideas**: Share your ideas and suggestions

---

## 🎉 **Happy Meeting Minutes Generation!**

Transform your meeting recordings into professional minutes with the power of AI. Save time, improve accuracy, and never miss important details again!

**Made with ❤️ for productive meetings**
