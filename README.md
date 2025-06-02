# 🚀 Transcriber

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/Sloth-on-meth/transcriber/releases)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-active-brightgreen.svg)](https://github.com/Sloth-on-meth/transcriber)

**Transcriber** is a blazing fast, multi-provider audio transcription tool for Dutch audio. It runs all providers in parallel, combines results with OpenAI GPT, and saves everything in organized folders. Perfect for podcasts, interviews, or any multi-speaker Dutch audio!

---

## 📋 Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Providers](#providers)
- [Example Output](#example-output)
- [Troubleshooting](#troubleshooting)
- [Changelog](#changelog)
- [Credits](#credits)

---
## ✨ Features

- ⚡️ Parallel transcription with multiple providers
- 🤖 Combines transcripts using OpenAI GPT
- 🛠️ Easy config via `config.json`
- 🎵 WAV & MP3 support
- 📝 Custom prompts for Whisper & Groq
- ⏱️ Configurable timeouts per provider
- 📁 Clean output per run, easy to find results

---

## 💻 Usage

Place your audio file in a folder (e.g. `to be transcribed/`). Then run:

```bash
python3 transcriber.py "to be transcribed/yourfile.wav"
```

All results are saved in a timestamped folder under `recordings/`.

---

## 🌐 Providers

This tool supports the following providers (runs all with API keys present):

- 🏢 **AssemblyAI**
- 🤖 **OpenAI Whisper (API)**
- ⚡ **Groq Whisper Large-v3 Turbo**
- 🗣️ **Speechmatics**

---

## 📦 Example Output

```
Transcribing yourfile.wav with all providers asynchronously...
[DEBUG] Starting transcription with AssemblyAI...
[DEBUG] Starting transcription with OpenAI Whisper...
[DEBUG] Starting transcription with Groq Whisper Large-v3 Turbo...
[DEBUG] Starting transcription with Speechmatics...
[DEBUG] ...

---
- AssemblyAI
- OpenAI Whisper
- Groq Whisper Large-v3 Turbo
- Speechmatics

======
Gecombineerde transcriptie (OpenAI GPT):
======

[Combined transcript here]

Combined transcript saved as recordings/run_YYYYMMDD_HHMMSS/Combined_OpenAI.txt
```

---

## 🛠️ Troubleshooting

- Make sure your `config.json` is valid and contains the correct API keys.
- Only providers with a valid API key will be used.
- If you get timeouts, try increasing the `timeout` value in your config.
- For best results, use clear Dutch audio in WAV or MP3 format.

---

## 📝 Changelog

See [changelog.md](changelog.md) for release notes and updates.

---

## 👤 Credits

Developed by [Sloth-on-meth](https://github.com/Sloth-on-meth) and contributors.

MIT License.

---

## Installation

### Using pip

```bash
pip install requests openai
```

### Using venv

Create a new virtual environment and install the required dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install requests openai
```

### Dependencies

- `requests` for API calls
- `openai` for OpenAI Whisper and ChatGPT integration


## Configuration

Create a `config.json` file in your project directory with your API keys and prompts:

### Example config.json

```json
{
  "assemblyai_api_key": "YOUR_ASSEMBLYAI_API_KEY",
  "openai_api_key": "YOUR_OPENAI_API_KEY",
  "groq_api_key": "YOUR_GROQ_API_KEY",
  "groq_whisper_endpoint": "https://api.groq.com/openai/v1/audio/transcriptions",

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