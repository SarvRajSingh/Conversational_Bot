import requests
import subprocess
import shutil

DG_API_KEY = "fa5e7eea81efdeaafa6132fc2b194f00d8d56837"
MODEL_NAME = "aura-asteria-en"

def is_installed(lib_name: str) -> bool:
    return shutil.which(lib_name) is not None

def send_tts_request(text):
    DEEPGRAM_URL = "https://api.deepgram.com/v1/speak"
    
    headers = {
        "Authorization": f"Token {DG_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "text": text
    }
    
    params = {
        "model": MODEL_NAME,
        "encoding": "linear16",
        "sample_rate": 24000
    }
    
    try:
        response = requests.post(DEEPGRAM_URL, headers=headers, json=payload, params=params, stream=True)
        response.raise_for_status()

        if is_installed("ffplay"):
            print("Playing audio...")
            ffplay_process = subprocess.Popen(
                ["ffplay", "-autoexit", "-nodisp", "-"],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            for chunk in response.iter_content(chunk_size=4096):
                if chunk:
                    ffplay_process.stdin.write(chunk)
            ffplay_process.stdin.close()
            ffplay_process.wait()
            print("Audio playback completed.")
        else:
            print("FFplay not found. Please install FFmpeg to play audio.")
    
    except requests.RequestException as e:
        print(f"Error making request to Deepgram API: {e}")
        if e.response is not None:
            print(f"Response status code: {e.response.status_code}")
            print(f"Response headers: {e.response.headers}")
            print(f"Response text: {e.response.text}")

# Example usage
text = "The returns for performance are superlinear."
send_tts_request(text)

print("Script execution completed.")