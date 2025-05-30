import os
import sys
# Suppress all stderr output (ALSA/JACK and other native warnings)
sys.stderr = open(os.devnull, 'w')
import contextlib
import pyaudio
import wave
import tempfile
import openai
import json
from datetime import datetime

# === CONFIG ===
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 5  # Duration per recording chunk
SAVE_INTERVAL_SECONDS = 300  # Save transcript every 5 minutes (300 seconds)

# Load OpenAI API key from config.json
with open('config.json') as f:
    config = json.load(f)
openai.api_key = config['openai_api_key']

def record_to_file(filename, duration):
    # Suppress ALSA/JACK and other audio backend warnings
    with open(os.devnull, 'w') as devnull, contextlib.redirect_stderr(devnull):
        audio = pyaudio.PyAudio()
        stream = audio.open(format=FORMAT, channels=CHANNELS,
                            rate=RATE, input=True,
                            frames_per_buffer=CHUNK)

        print(f"🎙️ Recording {duration}s...")
        frames = []
        for _ in range(0, int(RATE / CHUNK * duration)):
            data = stream.read(CHUNK)
            frames.append(data)

        stream.stop_stream()
        stream.close()
        audio.terminate()

        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(audio.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))

def transcribe(file_path):
    # Updated transcription logic for openai>=1.0.0
    with open(file_path, "rb") as audio_file:
        transcript = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return transcript.text

def save_transcript(text):
    # Create a new file with a timestamp in the filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"transcript_{timestamp}.txt"
    with open(filename, 'w') as f:
        f.write(text)
    print(f"Transcript saved to {filename}")

if __name__ == "__main__":
    print("Starting continuous transcription. Press Ctrl+C to stop.")
    buffer = []
    start_time = datetime.now()
    last_save_time = start_time
    try:
        while True:
            audio_filename = tempfile.mktemp(suffix='.wav')
            record_to_file(audio_filename, RECORD_SECONDS)
            transcript_text = transcribe(audio_filename)
            print(transcript_text)
            buffer.append(transcript_text)
            now = datetime.now()
            if (now - last_save_time).total_seconds() >= SAVE_INTERVAL_SECONDS:
                save_transcript('\n'.join(buffer))
                buffer = []
                last_save_time = now
    except KeyboardInterrupt:
        print("\nStopping continuous transcription.")
        if buffer:
            save_transcript('\n'.join(buffer))
