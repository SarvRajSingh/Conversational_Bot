import asyncio
import requests
import subprocess
import textwrap
import traceback
import keyboard
import time
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from deepgram import DeepgramClient, DeepgramClientOptions, LiveTranscriptionEvents, LiveOptions, Microphone

GROQ_API_KEY = "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"
DEEPGRAM_API_KEY = "fa5e7eea81efdeaafa6132fc2b194f00d8d56837"

class LanguageModelProcessor:
    def __init__(self):
        print("Initializing LanguageModelProcessor...")
        self.llm = ChatGroq(temperature=0, model_name="mixtral-8x7b-32768", groq_api_key=GROQ_API_KEY)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant."),
            ("human", "{text}")
        ])
        self.chain = self.prompt | self.llm
        print("LanguageModelProcessor initialized.")

    def process(self, text):
        print(f"LLM processing input: {text}")
        try:
            response = self.chain.invoke({"text": text})
            print(f"LLM response: {response.content}")
            return response.content
        except Exception as e:
            print(f"Error in LLM processing: {e}")
            print(traceback.format_exc())
            return None

class TextToSpeech:
    MODEL_NAME = "aura-asteria-en"

    def speak(self, text, character=None):
        print(f"TTS speaking: {text[:50]}...")  # Print first 50 chars of text
        DEEPGRAM_URL = "https://api.deepgram.com/v1/speak"
        headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
            "Content-Type": "application/json"
        }
        params = {
            "model": self.MODEL_NAME,
            "encoding": "linear16",
            "sample_rate": 24000
        }
        if character:
            params["voice"] = character

        chunks = textwrap.wrap(text, 1000, break_long_words=False, replace_whitespace=False)

        for chunk in chunks:
            payload = {"text": chunk}
            try:
                response = requests.post(DEEPGRAM_URL, headers=headers, json=payload, params=params, stream=True)
                response.raise_for_status()

                ffplay_process = subprocess.Popen(
                    ["ffplay", "-autoexit", "-nodisp", "-"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                for audio_chunk in response.iter_content(chunk_size=4096):
                    if audio_chunk:
                        ffplay_process.stdin.write(audio_chunk)
                ffplay_process.stdin.close()
                ffplay_process.wait()
            except requests.RequestException as e:
                print(f"Error in TTS: {e}")
                print(traceback.format_exc())

class ConversationManager:
    def __init__(self):
        self.llm = LanguageModelProcessor()
        self.tts = TextToSpeech()
        self.interrupt_event = asyncio.Event()

    def interrupt_response(self):
        self.interrupt_event.set()

    async def get_transcript(self):
        transcript = ""
        try:
            config = DeepgramClientOptions(options={"keepalive": "true"})
            deepgram = DeepgramClient(DEEPGRAM_API_KEY, config)
            dg_connection = deepgram.listen.asyncwebsocket.v("1")

            async def on_message(self, result, **kwargs):
                nonlocal transcript
                sentence = result.channel.alternatives[0].transcript
                if sentence and result.speech_final:
                    print(f"Final transcription: {sentence}")
                    transcript = sentence

            dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)

            options = LiveOptions(
                model="nova-2",
                punctuate=True,
                language="en-US",
                encoding="linear16",
                channels=1,
                sample_rate=16000,
                endpointing=1000
            )

            await dg_connection.start(options)
            microphone = Microphone(dg_connection.send)
            microphone.start()
            print("Speak now!")

            start_time = time.time()
            while not transcript and time.time() - start_time < 10:
                await asyncio.sleep(0.1)

            microphone.finish()
            await dg_connection.finish()

            print(f"Full transcript: {transcript}")
            return transcript.strip() if transcript else None

        except Exception as e:
            print(f"Error in speech recognition: {e}")
            print(traceback.format_exc())
            return None

    async def main(self):
        print("Available characters:")
        print("- Donald Trump")
        print("- Barack Obama")
        print("- Joe Biden")
        character = input("Select a character (or press Enter for default voice): ").strip()
        
        print("Press 'Esc' at any time to interrupt the response.")
        keyboard.on_press_key("esc", lambda _: self.interrupt_response())

        while True:
            try:
                print("Waiting for voice input...")
                user_input = await self.get_transcript()
                
                if not user_input:
                    print("No speech detected or empty transcript. Please try again.")
                    continue

                print(f"You said: {user_input}")

                if "goodbye" in user_input.lower():
                    print("Goodbye detected. Ending conversation.")
                    break

                print("Processing your input...")
                llm_response = self.llm.process(user_input)
                if llm_response is None:
                    print("Failed to get response from LLM. Please try again.")
                    continue
                
                print(f"Response: {llm_response}")
                print("Starting text-to-speech...")
                
                for chunk in textwrap.wrap(llm_response, 100):
                    if self.interrupt_event.is_set():
                        print("\nResponse interrupted.")
                        break
                    self.tts.speak(chunk, character if character else None)
                
                self.interrupt_event.clear()
                print("Response complete. Ready for next input.")
                
            except Exception as e:
                print(f"Error in main loop: {e}")
                print(traceback.format_exc())
                await asyncio.sleep(5)

if __name__ == "__main__":
    manager = ConversationManager()
    asyncio.run(manager.main())