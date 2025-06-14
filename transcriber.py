"""
Transcriber

A Python tool to transcribe audio files using multiple cloud STT providers in parallel (AssemblyAI, OpenAI Whisper, Groq Whisper, Speechmatics) and combine the results using OpenAI ChatGPT.

Usage:
    python transcriber.py <audiofile.wav>

Configuration:
    - See config.json for API keys and prompt customization.
    - Providers run in parallel for speed.
    - Each result is saved in recordings/<run_dir>/Provider.txt
    - Combined transcript is saved as Combined_OpenAI.txt

Author: sam
License: MIT
"""

import os
import sys
# Suppress all stderr output (ALSA/JACK and other native warnings)
# sys.stderr = open(os.devnull, 'w')  # DISABLED for debugging
import contextlib
import pyaudio
import wave
import tempfile
import requests
import json
from datetime import datetime
import boto3

# === CONFIG ===
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 30  # Duration per recording chunk (30 seconds)


# Load OpenAI API key from config.json
with open('config.json') as f:
    config = json.load(f)
assemblyai_api_key = config['assemblyai_api_key']

def record_to_file(filename, duration):
    """
    Record audio from the default microphone and save as a WAV file.

    Args:
        filename (str): Output filename for the WAV file.
        duration (int): Duration of the recording in seconds.
    """
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

def ensure_recordings_dir():
    """
    Ensure that the 'recordings' directory exists in the project root.
    Creates the directory if it does not exist.
    """
    if not os.path.exists('recordings'):
        os.makedirs('recordings')

def transcribe_assemblyai(file_path):
    """
    Transcribe audio using AssemblyAI API.

    Args:
        file_path (str): Path to the audio file.
    Returns:
        str: The transcribed text or an error message.
    """
    headers = {'authorization': assemblyai_api_key}
    with open(file_path, 'rb') as f:
        upload_response = requests.post('https://api.assemblyai.com/v2/upload', headers=headers, data=f)
    if upload_response.status_code != 200:
        return f"AssemblyAI upload failed: {upload_response.text}"
    upload_url = upload_response.json().get('upload_url')
    transcript_request = {'audio_url': upload_url, 'language_code': 'nl'}
    transcript_response = requests.post('https://api.assemblyai.com/v2/transcript', headers=headers, json=transcript_request)
    response_json = transcript_response.json()
    if 'id' not in response_json:
        return f"AssemblyAI error: {response_json}"
    transcript_id = response_json['id']
    while True:
        poll_response = requests.get(f'https://api.assemblyai.com/v2/transcript/{transcript_id}', headers=headers)
        status = poll_response.json()['status']
        if status == 'completed':
            return poll_response.json()['text']
        elif status == 'failed':
            return f"AssemblyAI transcription failed: {poll_response.json().get('error', 'Unknown error')}"
        import time; time.sleep(3)

def transcribe_speechmatics(file_path):
    """
    Transcribe audio using Speechmatics API.

    Args:
        file_path (str): Path to the audio file.
    Returns:
        str: The transcribed text or an error message.
    """
    import json as _json
    api_key = config.get('speechmatics_api_key')
    if not api_key:
        return "Speechmatics API key missing."
    url = "https://asr.api.speechmatics.com/v2/jobs/"
    headers = {"Authorization": f"Bearer {api_key}"}
    files = {"data_file": open(file_path, "rb")}
    data = {
        "config": _json.dumps({
            "type": "transcription",
            "transcription_config": {
                "language": "nl"
            }
        })
    }
    job_resp = requests.post(url, headers=headers, files=files, data=data)
    if job_resp.status_code != 201:
        return f"Speechmatics job error: {job_resp.text}"
    job_id = job_resp.json().get('id')
    import time
    while True:
        status_resp = requests.get(f"{url}{job_id}/", headers=headers)
        status = status_resp.json().get('job', {}).get('job_status')
        if status == 'done':
            transcript_url = f"{url}{job_id}/transcript?format=txt"
            transcript_resp = requests.get(transcript_url, headers=headers)
            return transcript_resp.text.strip()
        elif status == 'failed':
            return f"Speechmatics failed: {status_resp.text}"
        time.sleep(3)

def transcribe_openai_whisper(file_path):
    """
    Transcribe audio using OpenAI Whisper API.

    Args:
        file_path (str): Path to the audio file.
    Returns:
        str: The transcribed text or an error message.
    """
    try:
        import openai
        api_key = config.get('openai_api_key')
        if not api_key:
            return "OpenAI API key missing."
        prompt = config.get('prompt')
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            with open(file_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="nl",
                    prompt=prompt if prompt else None
                )
            return transcript.text
        except ImportError:
            openai.api_key = api_key
            with open(file_path, "rb") as audio_file:
                transcript = openai.Audio.transcribe(
                    model="whisper-1",
                    file=audio_file,
                    language="nl",
                    prompt=prompt if prompt else None
                )
            return transcript['text']
        except Exception as e:
            return f"OpenAI Whisper error: {e}"
    except Exception as e:
        return f"OpenAI Whisper error: {e}"

def transcribe_groq_whisper(file_path):
    """
    Transcribe audio using Groq Whisper API.

    Args:
        file_path (str): Path to the audio file.
    Returns:
        str: The transcribed text or an error message.
    """
    api_key = config.get('groq_api_key')
    endpoint = config.get('groq_whisper_endpoint')
    if not api_key or not endpoint:
        return "Groq config missing."
    headers = {
        'Authorization': f'Bearer {api_key}'
    }
    files = {
        'file': open(file_path, 'rb')
    }
    data = {
        'model': 'whisper-large-v3',
        'language': 'nl'
    }
    prompt = config.get('prompt')
    if prompt:
        data['prompt'] = prompt
    try:
        resp = requests.post(endpoint, headers=headers, files=files, data=data)
        if resp.status_code != 200:
            return f"Groq Whisper error: {resp.text}"
        return resp.json().get('text', str(resp.json()))
    except Exception as e:
        return f"Groq Whisper error: {e}"

def transcribe_aws(file_path):
    """
    Transcribe audio using AWS Transcribe.
    """
    # ... (existing code unchanged)


def transcribe_deepgram(file_path):
    """
    Transcribe audio using Deepgram API.
    """
    api_key = config.get('deepgram_api_key')
    if not api_key:
        return "Deepgram API key missing."
    url = "https://api.deepgram.com/v1/listen"
    headers = {
        "Authorization": f"Token {api_key}"
    }
    with open(file_path, 'rb') as f:
        audio = f.read()
    params = {
        "language": "nl"
    }
    try:
        resp = requests.post(url, headers=headers, params=params, data=audio)
        if resp.status_code != 200:
            return f"Deepgram error: {resp.text}"
        return resp.json()['results']['channels'][0]['alternatives'][0]['transcript']
    except Exception as e:
        return f"Deepgram error: {e}"


def transcribe_ibm(file_path):
    """
    Transcribe audio using IBM Watson Speech to Text.
    """
    api_key = config.get('ibm_api_key')
    url = config.get('ibm_url')
    if not api_key or not url:
        return "IBM Watson config missing."
    from requests.auth import HTTPBasicAuth
    with open(file_path, 'rb') as f:
        audio = f.read()
    headers = {
        'Content-Type': 'audio/wav',
    }
    params = {
        'model': 'nl-NL_BroadbandModel'
    }
    try:
        resp = requests.post(
            f"{url}/v1/recognize",
            headers=headers,
            params=params,
            data=audio,
            auth=HTTPBasicAuth('apikey', api_key)
        )
        if resp.status_code != 200:
            return f"IBM Watson error: {resp.text}"
        results = resp.json().get('results', [])
        transcript = ' '.join([alt['transcript'] for r in results for alt in r.get('alternatives', [])])
        return transcript.strip()
    except Exception as e:
        return f"IBM Watson error: {e}"


def transcribe_revai(file_path):
    """
    Transcribe audio using Rev AI API.
    """
    api_key = config.get('revai_api_key')
    if not api_key:
        return "Rev AI API key missing."
    url = "https://api.rev.ai/speechtotext/v1/jobs"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    # Upload file
    try:
        with open(file_path, 'rb') as f:
            upload_resp = requests.post(url, headers=headers, files={"media": f})
        if upload_resp.status_code not in [200, 201]:
            return f"Rev AI upload error: {upload_resp.text}"
        job_id = upload_resp.json()['id']
        # Poll for completion
        import time
        while True:
            status_resp = requests.get(f"https://api.rev.ai/speechtotext/v1/jobs/{job_id}", headers=headers)
            status = status_resp.json()['status']
            if status == 'transcribed':
                break
            elif status == 'failed':
                return f"Rev AI transcription failed: {status_resp.text}"
            time.sleep(5)
        # Get transcript
        transcript_resp = requests.get(f"https://api.rev.ai/speechtotext/v1/jobs/{job_id}/transcript?accept=application/json", headers=headers)
        if transcript_resp.status_code != 200:
            return f"Rev AI transcript error: {transcript_resp.text}"
        try:
            data = transcript_resp.json()
            # Rev AI returns monologues -> elements (type: text/punct)
            monologues = data.get('monologues', [])
            transcript = ''
            for mono in monologues:
                for el in mono.get('elements', []):
                    if el.get('type') in ('text', 'punct'):
                        transcript += el.get('value', '')
            return transcript.strip()
        except Exception:
            return transcript_resp.text.strip()
    except Exception as e:
        return f"Rev AI error: {e}"


def transcribe_vatis(file_path):
    """
    Transcribe audio using Vatis Tech API.
    """
    api_key = config.get('vatis_api_key')
    if not api_key:
        return "Vatis Tech API key missing."
    url = "https://vatis.tech/api/v1/speech-to-text/asr"
    headers = {
        "x-api-key": api_key
    }
    files = {
        'file': open(file_path, 'rb')
    }
    data = {
        'language': 'nl'
    }
    try:
        resp = requests.post(url, headers=headers, files=files, data=data)
        if resp.status_code != 200:
            return f"Vatis Tech error: {resp.text}"
        return resp.json()['result']['text']
    except Exception as e:
        return f"Vatis Tech error: {e}"


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



import shutil





def ensure_recordings_dir():
    if not os.path.exists('recordings'):
        os.makedirs('recordings')

def transcribe_assemblyai(file_path):
    headers = {'authorization': assemblyai_api_key}
    with open(file_path, 'rb') as f:
        upload_response = requests.post('https://api.assemblyai.com/v2/upload', headers=headers, data=f)
    if upload_response.status_code != 200:
        return f"AssemblyAI upload failed: {upload_response.text}"
    upload_url = upload_response.json().get('upload_url')
    transcript_request = {'audio_url': upload_url, 'language_code': 'nl'}
    # Do NOT send prompt: Universal model does not support it
    transcript_response = requests.post('https://api.assemblyai.com/v2/transcript', json=transcript_request, headers=headers)
    response_json = transcript_response.json()
    if 'id' not in response_json:
        return f"AssemblyAI error: {response_json}"
    transcript_id = response_json['id']
    while True:
        poll_response = requests.get(f'https://api.assemblyai.com/v2/transcript/{transcript_id}', headers=headers)
        status = poll_response.json()['status']
        if status == 'completed':
            return poll_response.json()['text']
        elif status == 'failed':
            return f"AssemblyAI transcription failed: {poll_response.json().get('error', 'Unknown error')}"
        import time; time.sleep(3)


def transcribe_speechmatics(file_path):
    import json as _json
    api_key = config.get('speechmatics_api_key')
    if not api_key:
        return "Speechmatics API key missing."
    url = "https://asr.api.speechmatics.com/v2/jobs/"
    headers = {"Authorization": f"Bearer {api_key}"}
    files = {"data_file": open(file_path, "rb")}
    # Speechmatics v2 expects 'config' as a JSON string
    data = {
        "config": _json.dumps({
            "type": "transcription",
            "transcription_config": {
                "language": "nl"
            }
        })
    }
    job_resp = requests.post(url, headers=headers, files=files, data=data)
    if job_resp.status_code != 201:
        return f"Speechmatics job error: {job_resp.text}"
    job_id = job_resp.json().get('id')
    # Poll for completion
    import time
    while True:
        status_resp = requests.get(f"{url}{job_id}/", headers=headers)
        status = status_resp.json().get('job', {}).get('job_status')
        if status == 'done':
            # Get transcript
            transcript_url = f"{url}{job_id}/transcript?format=txt"
            transcript_resp = requests.get(transcript_url, headers=headers)
            return transcript_resp.text.strip()
        elif status == 'failed':
            return f"Speechmatics failed: {status_resp.text}"
        time.sleep(3)

def transcribe_openai_whisper(file_path):
    try:
        import openai
        api_key = config.get('openai_api_key')
        if not api_key:
            return "OpenAI API key missing."
        prompt = config.get('prompt')
        try:
            # Try new openai>=1.0.0 interface
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            with open(file_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="nl",
                    prompt=prompt if prompt else None
                )
            return transcript.text
        except ImportError:
            # Fallback to legacy
            openai.api_key = api_key
            with open(file_path, "rb") as audio_file:
                transcript = openai.Audio.transcribe(
                    model="whisper-1",
                    file=audio_file,
                    language="nl",
                    prompt=prompt if prompt else None
                )
            return transcript['text']
        except Exception as e:
            return f"OpenAI Whisper error: {e}"
    except Exception as e:
        return f"OpenAI Whisper error: {e}"

def transcribe_groq_whisper(file_path):
    api_key = config.get('groq_api_key')
    endpoint = config.get('groq_whisper_endpoint')
    if not api_key or not endpoint:
        return "Groq config missing."
    headers = {
        'Authorization': f'Bearer {api_key}'
    }
    files = {
        'file': open(file_path, 'rb')
    }
    data = {
        'model': 'whisper-large-v3',
        'language': 'nl'
    }
    prompt = config.get('prompt')
    if prompt:
        data['prompt'] = prompt
    try:
        resp = requests.post(endpoint, headers=headers, files=files, data=data)
        if resp.status_code != 200:
            return f"Groq Whisper error: {resp.text}"
        return resp.json().get('text', str(resp.json()))
    except Exception as e:
        return f"Groq Whisper error: {e}"

if __name__ == "__main__":
    import sys
    import time
    import concurrent.futures
    from datetime import datetime
    import os

    if len(sys.argv) != 2:
        print("Usage: python transcriber.py <audiofile.wav>")
        sys.exit(1)
    audio_filename = sys.argv[1]
    if not os.path.isfile(audio_filename):
        print(f"File not found: {audio_filename}")
        sys.exit(1)

    # Create a new subfolder in 'recordings' for this run
    ensure_recordings_dir()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    run_dir = os.path.join('recordings', f'run_{timestamp}')
    os.makedirs(run_dir, exist_ok=True)

    providers = []
    def not_empty(val):
        return val is not None and str(val).strip() != ''

    providers = []
    if not_empty(config.get('assemblyai_api_key')):
        print("[INFO] Using AssemblyAI provider")
        providers.append(("AssemblyAI", transcribe_assemblyai))
    else:
        print("[INFO] Skipping AssemblyAI (no API key)")
    if not_empty(config.get('openai_api_key')):
        print("[INFO] Using OpenAI Whisper provider")
        providers.append(("OpenAI Whisper", transcribe_openai_whisper))
    else:
        print("[INFO] Skipping OpenAI Whisper (no API key)")
    if not_empty(config.get('groq_api_key')) and not_empty(config.get('groq_whisper_endpoint')):
        print("[INFO] Using Groq Whisper provider")
        providers.append(("Groq Whisper Large-v3 Turbo", transcribe_groq_whisper))
    else:
        print("[INFO] Skipping Groq Whisper (missing API key or endpoint)")
    if not_empty(config.get('speechmatics_api_key')):
        print("[INFO] Using Speechmatics provider")
        providers.append(("Speechmatics", transcribe_speechmatics))
    else:
        print("[INFO] Skipping Speechmatics (no API key)")
    if not_empty(config.get('aws_access_key_id')) and not_empty(config.get('aws_secret_access_key')) and not_empty(config.get('aws_region')):
        print("[INFO] Using AWS Transcribe provider")
        providers.append(("AWS Transcribe", transcribe_aws))
    else:
        print("[INFO] Skipping AWS Transcribe (missing credentials)")
    if not_empty(config.get('deepgram_api_key')):
        print("[INFO] Using Deepgram provider")
        providers.append(("Deepgram", transcribe_deepgram))
    else:
        print("[INFO] Skipping Deepgram (no API key)")
    if not_empty(config.get('ibm_api_key')) and not_empty(config.get('ibm_url')):
        print("[INFO] Using IBM Watson provider")
        providers.append(("IBM Watson Speech to Text", transcribe_ibm))
    else:
        print("[INFO] Skipping IBM Watson (missing API key or URL)")
    # if not_empty(config.get('revai_api_key')):
    #     print("[INFO] Using Rev AI provider")
    #     providers.append(("Rev AI", transcribe_revai))
    # else:
    #     print("[INFO] Skipping Rev AI (no API key)")
    # Rev AI disabled: output format not currently usable for Dutch transcription.
    if not_empty(config.get('vatis_api_key')):
        print("[INFO] Using Vatis Tech provider")
        providers.append(("Vatis Tech", transcribe_vatis))
    else:
        print("[INFO] Skipping Vatis Tech (no API key)")
    if not providers:
        print("[ERROR] No providers enabled. Please add at least one API key to config.json.")
        sys.exit(1)
    results = [None] * len(providers)
    print(f"Transcribing {audio_filename} with all providers asynchronously...")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_idx = {}
        for idx, (name, func) in enumerate(providers):
            print(f"[DEBUG] Starting transcription with {name}...")
            future = executor.submit(func, audio_filename)
            future_to_idx[future] = idx
        any_results = False
        for future in concurrent.futures.as_completed(future_to_idx):
            idx = future_to_idx[future]
            name, _ = providers[idx]
            try:
                result = future.result()
                print(f"[DEBUG] {name} finished. Result: {result[:100] if isinstance(result, str) else result}")
                any_results = True
            except Exception as exc:
                result = f"Exception: {exc}"
                print(f"[ERROR] Exception from {name}: {exc}")
            results[idx] = (name, result)
            print(f"\n---\n- {name}\n- {result}\n")
            output_file = os.path.join(run_dir, f"{name.replace(' ', '_')}.txt")
            with open(output_file, 'w', encoding='utf-8') as out_f:
                out_f.write(result if isinstance(result, str) else str(result))
        if not any_results:
            print("[ERROR] No transcription results returned from any provider.")

    print(f"\nAll transcriptions saved in {run_dir}\n")

    # Combine all results and send to OpenAI ChatGPT
    openai_api_key = config.get('openai_api_key')
    if not openai_api_key:
        print("OpenAI API key missing in config.json, cannot combine transcriptions.")
        sys.exit(1)
    try:
        import openai
        combine_prompt = config.get('combine_prompt') or "dit zijn verschillende transcripties van 1 opname van een DND sessie. maak er 1 coherente transcriptie van"
        transcript_texts = "\n\n".join([
            f"{name}:\n{text}" for name, text in results
        ])
        system_message = {"role": "system", "content": combine_prompt}
        user_message = {"role": "user", "content": transcript_texts}
        try:
            # Try new openai>=1.0.0 interface
            from openai import OpenAI
            client = OpenAI(api_key=openai_api_key)
            chat_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[system_message, user_message]
            )
            combined = chat_response.choices[0].message.content.strip()
        except ImportError:
            # Legacy fallback
            openai.api_key = openai_api_key
            chat_response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[system_message, user_message]
            )
            combined = chat_response["choices"][0]["message"]["content"].strip()
        print("\n======\nGecombineerde transcriptie (OpenAI GPT):\n======\n")
        print(combined)
        combined_path = os.path.join(run_dir, "Combined_OpenAI.txt")
        with open(combined_path, 'w') as f:
            f.write(combined)
        print(f"\nCombined transcript saved as {combined_path}\n")
    except Exception as e:
        print(f"Error combining transcripts with OpenAI: {e}")
