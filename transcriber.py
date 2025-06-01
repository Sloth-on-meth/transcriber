import os
import sys
# Suppress all stderr output (ALSA/JACK and other native warnings)
sys.stderr = open(os.devnull, 'w')
import contextlib
import pyaudio
import wave
import tempfile
import requests
import json
from datetime import datetime

# === CONFIG ===
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 6  # Duration per recording chunk (1 minute)


# Load OpenAI API key from config.json
with open('config.json') as f:
    config = json.load(f)
assemblyai_api_key = config['assemblyai_api_key']

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
    # Transcription logic for AssemblyAI, with Dutch language and DND prompt
    headers = {
        'authorization': assemblyai_api_key,
    }
    # Upload audio file
    with open(file_path, 'rb') as f:
        upload_response = requests.post('https://api.assemblyai.com/v2/upload',
                                       headers=headers, data=f)
    if upload_response.status_code != 200:
        print(f"Upload failed with status code {upload_response.status_code}")
        print(f"Response text: {upload_response.text}")
        sys.exit(1)
    try:
        upload_url = upload_response.json()['upload_url']
    except Exception as e:
        print(f"Failed to decode upload response as JSON: {e}")
        print(f"Raw response: {upload_response.text}")
        sys.exit(1)

    # Start transcription
    transcript_request = {
        'audio_url': upload_url,
        'language_code': 'nl'
    }
    transcript_response = requests.post('https://api.assemblyai.com/v2/transcript',
                                        json=transcript_request, headers=headers)
    response_json = transcript_response.json()
    if 'id' not in response_json:
        print("Error: Unexpected response from AssemblyAI when requesting transcription.")
        print("Status code:", transcript_response.status_code)
        print("Response JSON:", response_json)
        sys.exit(1)
    transcript_id = response_json['id']

    # Poll for completion
    while True:
        poll_response = requests.get(f'https://api.assemblyai.com/v2/transcript/{transcript_id}', headers=headers)
        status = poll_response.json()['status']
        if status == 'completed':
            return poll_response.json()['text']
        elif status == 'failed':
            raise Exception('Transcription failed: ' + poll_response.json().get('error', 'Unknown error'))
        import time; time.sleep(3)



if __name__ == "__main__":
    print("Starting 1-minute transcription loop. Press Ctrl+C to stop.")
    output_file = "transcriptions.txt"
    try:
        while True:
            audio_filename = tempfile.mktemp(suffix='.wav')
            record_to_file(audio_filename, RECORD_SECONDS)
            transcript_text = transcribe(audio_filename)
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(output_file, 'a') as f:
                f.write(f"[{timestamp}]\n{transcript_text}\n\n")
            print(f"Saved transcription at {timestamp} to {output_file}.")
    except KeyboardInterrupt:
        print("\nStopping continuous transcription.")
