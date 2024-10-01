import requests
import random
import pyttsx3
from PIL import Image, ImageDraw, ImageFont
import io
import openai
import os
import wave
import pyaudio
from openai import OpenAI

# Function to safely get the API key
def get_api_key():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        api_key = input("Please enter your OpenAI API key: ")
        os.environ["OPENAI_API_KEY"] = api_key
    return api_key

# Get and set the API key
api_key = get_api_key()

# Print API Key for troubleshooting (only the first few characters)
print(f"API Key: {api_key[:8]}...")

# Initialize OpenAI client
try:
    client = OpenAI(api_key=api_key)
    # Test the API key with a simple request
    client.models.list()
except openai.AuthenticationError:
    print("Error: Invalid API key. Please check your API key and try again.")
    exit(1)
except Exception as e:
    print(f"An error occurred while initializing the OpenAI client: {e}")
    exit(1)

# Function to fetch random quotes for personality
def get_random_quote():
    try:
        response = requests.get("https://api.quotable.io/random")
        if response.status_code == 200:
            return response.json()['content']
        else:
            return "Life is what happens when you're busy making other plans."
    except:
        return "The only way to do great work is to love what you do."

# Function to create a card image
def create_card(personality):
    width, height = 400, 300
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except IOError:
        font = ImageFont.load_default()
    
    y_position = 20
    for key, value in personality.items():
        text = f"{key}: {value}"
        draw.text((20, y_position), text, fill='black', font=font)
        y_position += 40
    
    return image

# Function to generate and save cards
def generate_and_save_cards(names):
    personalities = [generate_personality(name) for name in names]
    for i, personality in enumerate(personalities):
        card = create_card(personality)
        card.save(f"personality_card_{i+1}.png")
    print(f"{len(names)} personality cards have been generated and saved as PNG files.")
    return personalities

# Function to speak text
def speak(text, personality):
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    
    # Set voice based on personality
    if personality['Name'] in ['Taylor Swift', 'Greta Thunberg']:
        # Use a female voice if available
        female_voice = next((voice for voice in voices if voice.gender == 'female'), None)
        if female_voice:
            engine.setProperty('voice', female_voice.id)
    else:
        # Use a male voice for other personalities
        male_voice = next((voice for voice in voices if voice.gender == 'male'), None)
        if male_voice:
            engine.setProperty('voice', male_voice.id)
    
    # Adjust speech rate and pitch based on personality
    if personality['Name'] == 'Donald Trump':
        engine.setProperty('rate', 150)  # Slower speech
        engine.setProperty('pitch', 75)  # Lower pitch
    elif personality['Name'] == 'Taylor Swift':
        engine.setProperty('rate', 170)  # Slightly faster
        engine.setProperty('pitch', 110)  # Higher pitch
    
    engine.say(text)
    engine.runAndWait()

# Function to listen to user input
def listen():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    RECORD_SECONDS = 5

    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("Listening...")
    frames = []

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("Finished recording.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    # Save the recorded audio
    wf = wave.open("temp_audio.wav", 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    # Use OpenAI's Whisper API for speech recognition
    try:
        with open("temp_audio.wav", "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
        os.remove("temp_audio.wav")  # Clean up the temporary file
        return transcript.text
    except openai.RateLimitError:
        print("Error: API quota exceeded. Switching to text input.")
        return input("You (text): ")
    except Exception as e:
        print(f"An error occurred during speech recognition: {e}")
        return input("You (text): ")

# Function to generate a personality with specific traits
def generate_personality(name):
    personalities = {
        "Robert Downey Jr.": {
            "Work": "Actor",
            "Personality": "Charismatic",
            "Nature": "Witty",
            "Quote": "I think you end up doing the stuff you were supposed to do at the time you were supposed to do it."
        },
        "Donald Trump": {
            "Work": "Businessman and Former U.S. President",
            "Personality": "Assertive and Controversial",
            "Nature": "Outspoken",
            "Quote": "Make America Great Again!",
            "Speech_style": "Uses simple language, often repeats phrases for emphasis. Tends to use superlatives like 'the best', 'huge', 'tremendous'. Often starts sentences with 'Believe me' or 'Many people are saying'. Frequently mentions his own accomplishments."
        },
        "Elon Musk": {
            "Work": "Entrepreneur and Innovator",
            "Personality": "Visionary",
            "Nature": "Ambitious",
            "Quote": "When something is important enough, you do it even if the odds are not in your favor."
        },
        "Taylor Swift": {
            "Work": "Singer-Songwriter",
            "Personality": "Creative and Empathetic",
            "Nature": "Genuine and Relatable",
            "Quote": "Just be yourself, there is no one better.",
            "Speech_style": "Speaks with enthusiasm and warmth. Uses relatable metaphors and personal anecdotes. Often references her songs or experiences in the music industry."
        },
        "Greta Thunberg": {
            "Work": "Climate Activist",
            "Personality": "Determined",
            "Nature": "Passionate",
            "Quote": "You are never too small to make a difference."
        }
    }
    
    personality = personalities.get(name, {
        "Work": random.choice(["Entrepreneur", "Scientist", "Artist", "Teacher", "Doctor"]),
        "Personality": random.choice(["Introverted", "Extroverted", "Analytical", "Creative", "Ambitious"]),
        "Nature": random.choice(["Kind", "Assertive", "Calm", "Energetic", "Thoughtful"]),
        "Quote": get_random_quote()
    })
    
    personality["Name"] = name
    personality["Confidence"] = f"{random.randint(60, 100)}%"
    return personality

# Function to generate a response using GPT
def generate_response(personality, conversation_history):
    prompt = f"""You are {personality['Name']}, a {personality['Nature']} {personality['Work']} with a {personality['Personality']} personality. Your confidence level is {personality['Confidence']}. 
    Speech style: {personality.get('Speech_style', 'Speak naturally.')}
    Respond to the following conversation in the style of {personality['Name']}. Keep responses concise, within 2-3 sentences. Incorporate aspects of your work, personality, and experiences into your responses:

    {' '.join(conversation_history[-5:])}  # Only use the last 5 conversation entries for context
    {personality['Name']}:"""
    
    try:
        response = client.completions.create(
            model="text-davinci-002",
            prompt=prompt,
            max_tokens=100,
            n=1,
            stop=None,
            temperature=0.8,
        )
        return response.choices[0].text.strip()
    except Exception as e:
        print(f"An error occurred while generating a response: {e}")
        return "I'm sorry, I'm having trouble responding right now."

# Function to have a conversation with a personality
def converse_with_personality(personality):
    conversation_history = [f"AI: Hello, I'm {personality['Name']}. {personality['Quote']}"]
    print(conversation_history[-1])
    speak(conversation_history[-1], personality)
    
    while True:
        choice = input("Choose input method (voice/text): ").lower()
        if choice == 'voice':
            user_input = listen()
        elif choice == 'text':
            user_input = input("You: ")
        else:
            print("Invalid choice. Please choose 'voice' or 'text'.")
            continue

        if user_input:
            conversation_history.append(f"Human: {user_input}")
            
            if "bye" in user_input.lower():
                response = "It was nice talking to you. Goodbye!"
                print(f"{personality['Name']}: {response}")
                speak(response, personality)
                break
            
            response = generate_response(personality, conversation_history)
            conversation_history.append(f"AI: {response}")
            print(f"{personality['Name']}: {response}")
            speak(response, personality)

def record_audio(filename, duration=5):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100

    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print(f"Recording for {duration} seconds...")
    frames = []

    for i in range(0, int(RATE / CHUNK * duration)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("Recording finished.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

if __name__ == "__main__":
    names = ["Robert Downey Jr.", "Donald Trump", "Elon Musk", "Taylor Swift", "Greta Thunberg"]
    personalities = generate_and_save_cards(names)
    
    print("Choose a personality to talk to:")
    for i, p in enumerate(personalities):
        print(f"{i+1}. {p['Name']}")
    
    while True:
        choice = input("Enter the number or name of the personality you want to talk to: ")
        try:
            if choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(personalities):
                    chosen_personality = personalities[index]
                    break
            else:
                chosen_personality = next((p for p in personalities if p['Name'].lower() == choice.lower()), None)
                if chosen_personality:
                    break
            print("Invalid choice. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number or a name.")
    
    print(f"You've chosen to talk to {chosen_personality['Name']}.")
    converse_with_personality(chosen_personality)