# Transcriber

This project takes an audio file (e.g., WAV or MP3), sends it to multiple speech-to-text (STT) providers in parallel, and saves each transcription to a separate file. Providers supported:
- AssemblyAI
- OpenAI Whisper (API)
- Groq Whisper Large-v3 Turbo
- Google Cloud Speech-to-Text

All transcriptions are run asynchronously for speed. Results are printed to the console as they arrive and saved in a new timestamped subfolder in the `recordings/` directory for each run.


## Features

- Parallel transcription with multiple providers
- Combines transcripts using OpenAI GPT
- Easy config via `config.json`
- WAV file support
- Support for prompts in OpenAI Whisper and Groq Whisper
- Asynchronous transcription for improved speed
- Automatic handling of AssemblyAI's Universal model

## Installation

### Using pip

```bash
pip install requests openai google-cloud-speech
```

### Using venv

Create a new virtual environment and install the required dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install requests openai google-cloud-speech
```

### Dependencies

- `requests` for API calls
- `openai` for OpenAI Whisper and ChatGPT integration
- `google-cloud-speech` for Google Cloud Speech-to-Text integration

## Configuration

Create a `config.json` file in your project directory with your API keys and prompts:

### Example config.json

```json
{
  "assemblyai_api_key": "YOUR_ASSEMBLYAI_API_KEY",
  "openai_api_key": "YOUR_OPENAI_API_KEY",
  "groq_api_key": "YOUR_GROQ_API_KEY",
  "groq_whisper_endpoint": "https://api.groq.com/openai/v1/audio/transcriptions",
  "google_application_credentials": "path/to/your_google_service_account.json",
  "prompt": "Transcribe the following Dutch audio as accurately as possible.",
  "combine_prompt": "You will receive multiple transcripts of the same audio file. Combine these into a single transcript that is as accurate and complete as possible, without summarizing. Preserve original sentences, order, and details. Only correct errors if absolutely necessary for clarity. Do not add anything that was not in the original transcripts."
}
```

- The `prompt` field is optional and will be used by providers that support it (OpenAI Whisper, Groq Whisper).
- The `combine_prompt` field is used as the system prompt when sending all STT results to OpenAI ChatGPT for the final, combined transcript. If not set, a default Dutch DND prompt is used.
- AssemblyAI currently does not support prompts for the default Universal model (the script handles this automatically).
- All API keys are required for their respective providers.

## Usage

1. Install dependencies:
   ```bash
   pip install requests openai google-cloud-speech
   ```
2. Run the script with an audio file:
   ```bash
   python transcriber.py path/to/your_audio.wav
   ```
3. Each run creates a new timestamped folder in `recordings/` (e.g., `recordings/run_20250601_224825/`).
4. Each provider's output is saved as a separate text file in that folder (e.g., `AssemblyAI.txt`, `Speechmatics.txt`, etc.).
5. Results are printed to the console as soon as they are ready.

## Google Cloud Setup
- Create a Google Cloud project and enable the Speech-to-Text API.
- Create a service account and download the JSON key file.
- Add the path to this file as `google_application_credentials` in your config.json.
- The script will use this key for authentication.

## Notes
- This project is experimental. Accuracy and reliability depend on the external STT providers.
- Feedback and contributions are welcome!