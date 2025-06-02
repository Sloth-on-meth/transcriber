# Transcriber

This project takes an audio file (e.g., WAV or MP3), sends it to multiple speech-to-text (STT) providers in parallel, and saves each transcription to a separate file. Providers supported:
- AssemblyAI
- OpenAI Whisper (API)
- Groq Whisper Large-v3 Turbo
- Google Cloud Speech-to-Text

All transcriptions are run asynchronously for speed. Results are printed to the console as they arrive and saved in a new timestamped subfolder in the `recordings/` directory for each run.

After all transcriptions are finished, the script sends them to OpenAI ChatGPT with the following prompt (in Dutch):

```
dit zijn verschillende transcripties van 1 opname van een DND sessie. maak er 1 coherente transcriptie van
```

The combined, coherent transcript is printed to the console and saved as `Combined_OpenAI.txt` in the same run folder.

## Example config.json

Create a `config.json` file in your project directory with your API keys and prompts:

```json
{
  "assemblyai_api_key": "YOUR_ASSEMBLYAI_API_KEY",
  "openai_api_key": "YOUR_OPENAI_API_KEY",
  "groq_api_key": "YOUR_GROQ_API_KEY",
  "groq_whisper_endpoint": "https://api.groq.com/openai/v1/audio/transcriptions",
  "google_application_credentials": "path/to/your_google_service_account.json",
  "prompt": "Optional prompt for STT providers that support it.",
  "combine_prompt": "System prompt for combining all transcriptions into one coherent text."
}
```

- The `google_application_credentials` field should point to your Google Cloud service account JSON key file. See below for setup instructions.
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