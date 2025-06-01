# Transcriber

This project takes an audio file (e.g., WAV or MP3), sends it to multiple speech-to-text (STT) providers in parallel, and saves each transcription to a separate file. Providers supported:
- AssemblyAI
- OpenAI Whisper (API)
- Groq Whisper Large-v3 Turbo

All transcriptions are run asynchronously for speed. Results are printed to the console as they arrive and saved in a new timestamped subfolder in the `recordings/` directory for each run.

After all transcriptions are finished, the script sends them to OpenAI ChatGPT with the following prompt (in Dutch):

```
dit zijn verschillende transcripties van 1 opname van een DND sessie. maak er 1 coherente transcriptie van
```

The combined, coherent transcript is printed to the console and saved as `Combined_OpenAI.txt` in the same run folder.

## Example config.json

Create a `config.json` file in your project directory with your API keys and an optional prompt:

```json
{
  "assemblyai_api_key": "YOUR_ASSEMBLYAI_API_KEY",
  "speechmatics_api_key": "YOUR_SPEECHMATICS_API_KEY",
  "openai_api_key": "YOUR_OPENAI_API_KEY",
  "groq_api_key": "YOUR_GROQ_API_KEY",
  "groq_whisper_endpoint": "https://api.groq.com/openai/v1/audio/transcriptions",
  "prompt": "DND. 4 karakters. Grim, Gerrit, Fenomin en Bobbel. Gerrit gespeeld door sam, fenomin gespeeld door marc, bobbel gespeeld door diego, grim gespeeld door daan. DM heet amber. we doen de curse of strahd campaign."
}
```

- The `prompt` field is optional and will be used by providers that support it (OpenAI Whisper, Groq Whisper).
- AssemblyAI currently does not support prompts for the default Universal model (the script handles this automatically).
- All API keys are required for their respective providers.

## Usage

1. Install dependencies:
   ```bash
   pip install requests openai
   ```
2. Run the script with an audio file:
   ```bash
   python transcriber.py path/to/your_audio.wav
   ```
3. Each run creates a new timestamped folder in `recordings/` (e.g., `recordings/run_20250601_224825/`).
4. Each provider's output is saved as a separate text file in that folder (e.g., `AssemblyAI.txt`, `Speechmatics.txt`, etc.).
5. Results are printed to the console as soon as they are ready.

## Notes
- This project is experimental. Accuracy and reliability depend on the external STT providers.
- Feedback and contributions are welcome!