import asyncio
import pyaudio
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
)

class TranscriptCollector:
    def __init__(self):
        self.reset()

    def reset(self):
        self.transcript_parts = []

    def add_part(self, part):
        self.transcript_parts.append(part)

    def get_full_transcript(self):
        return ' '.join(self.transcript_parts)

transcript_collector = TranscriptCollector()

async def get_transcript():
    try:
        config = DeepgramClientOptions(options={"keepalive": "true"})
        deepgram: DeepgramClient = DeepgramClient("fa5e7eea81efdeaafa6132fc2b194f00d8d56837", config)

        dg_connection = deepgram.listen.asynclive.v("1")

        async def on_message(self, result, **kwargs):
            sentence = result.channel.alternatives[0].transcript

            if sentence:  # Only process non-empty transcripts
                if result.speech_final:
                    print(f"Transcription: {sentence}")
                    transcript_collector.reset()
                else:
                    transcript_collector.add_part(sentence)

        async def on_error(self, error, **kwargs):
            print(f"Error: {error}")

        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        dg_connection.on(LiveTranscriptionEvents.Error, on_error)

        options = LiveOptions(
            model="nova-2",
            punctuate=True,
            language="en-US",
            encoding="linear16",
            channels=1,
            sample_rate=16000,
            endpointing=True
        )

        await dg_connection.start(options)

        microphone = Microphone(dg_connection.send)

        microphone.start()
        print("Microphone started. Speak now!")

        while True:
            if not microphone.is_active():
                break
            await asyncio.sleep(0.1)

        microphone.finish()
        dg_connection.finish()

    except Exception as e:
        print(f"Error: {e}")
        return

if __name__ == "__main__":
    asyncio.run(get_transcript())