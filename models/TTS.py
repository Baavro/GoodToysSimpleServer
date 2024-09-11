import numpy as np
from cartesia import Cartesia
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    PrerecordedOptions,
    FileSource,
    SpeakOptions
)
DEEPGRAM_API_KEY = "38712ae34cba726a1f351ca0fd451c1e7b88bd6d"

class TTSModel:    
    def __init__(self,model='aura'):
        self.model = model
        if self.model == 'cartesia':
            CARTESIA_API_KEY = "bb591482-d058-467f-96b9-6a89e2ea2555"
            self.TTS = Cartesia(api_key=CARTESIA_API_KEY)
            self.voice_name = "California Girl"
            self.voice = self.TTS.voices.get(id="a0e99841-438c-4a64-b679-ae501e7d6091")

            # You can find the supported `output_format`s at https://docs.cartesia.ai/api-reference/endpoints/stream-speech-server-sent-events
            self.output_format = {
                "container": "raw",
                "encoding": "pcm_s16le",
                "sample_rate": 16000,
            }
        
        if self.model == 'aura':
            self.deepgram: DeepgramClient = DeepgramClient(DEEPGRAM_API_KEY, None)


    def generate_speech(self, text, alpha=0.3, beta=0.7, diffusion_steps=5, embedding_scale=1):        
        if self.model == 'cartesia':
            all_audio_data = bytearray()
            # Generate and stream audio
            for output in self.TTS.tts.sse(
                model_id="sonic-english",
                transcript=text,
                voice_embedding=self.voice["embedding"],
                stream=True,
                output_format=self.output_format,
            ):
                buffer = output["audio"]
                # Append to our list of audio data
                all_audio_data.extend(buffer)
            return all_audio_data
        
        if self.model == 'aura':
            options = SpeakOptions(
                    model="aura-asteria-en",
                    sample_rate=16000,
                    encoding="linear16",
                    container="wav"
                )
            # STEP 3: Call the save method on the speak property
            SPEAK_TEXT = {"text": text}
            response = self.deepgram.speak.rest.v("1").stream_raw(SPEAK_TEXT, options)

            return response
        
    def _amplify_audio(self, audio, gain=10):
        amplified = np.clip(audio * gain, -1, 1)
        return (amplified * 32767).astype(np.int16)