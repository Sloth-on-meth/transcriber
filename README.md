# Transcriber

This project records 30 seconds of audio, sends it to multiple speech-to-text (STT) providers in parallel, and saves the transcriptions to a file. Providers supported:
- AssemblyAI
- Speechmatics
- OpenAI Whisper (API)
- Groq Whisper Large-v3 Turbo

All transcriptions are run asynchronously for speed. Results are printed to the console as they arrive and saved in the `recordings/` directory.

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
2. Run the script:
   ```bash
   python transcriber.py
   ```
3. Speak for 30 seconds. Transcriptions will be printed to the console and saved in the `recordings/` folder.

## Notes
- This project is experimental. Accuracy and reliability depend on the external STT providers.
- Feedback and contributions are welcome!