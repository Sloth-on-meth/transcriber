import pyaudio
import wave
import tempfile
import openai
import os
import json
from datetime import datetime

# === CONFIG ===
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 5  # Duration per recording

# Load OpenAI API key from config.json
with open('config.json') as f:
    config = json.load(f)
openai.api_key = config['openai_api_key']

def record_to_file(filename, duration):
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
    # Example transcription logic (replace with your actual code)
    with open(file_path, 'rb') as audio_file:
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
    return transcript['text']

def save_transcript(text):
    # Create a new file with a timestamp in the filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"transcript_{timestamp}.txt"
    with open(filename, 'w') as f:
        f.write(text)
    print(f"Transcript saved to {filename}")

if __name__ == "__main__":
    audio_filename = tempfile.mktemp(suffix='.wav')
    record_to_file(audio_filename, RECORD_SECONDS)
    transcript_text = transcribe(audio_filename)
    save_transcript(transcript_text)
