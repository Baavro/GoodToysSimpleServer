import torch
from groq import Groq

class STTModel:
    def __init__(self, model='groq'):
        self.model_name = model
            
        if self.model_name == 'groq':
            api_key="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"
            self.client = Groq(api_key=api_key)

    def transcribe(self, audio_file):
        if self.model_name == 'groq':
            with open(audio_file, "rb") as file:
                # Create a transcription of the audio file
                transcription = self.client.audio.transcriptions.create(
                file=(audio_file, file.read()), # Required audio file
                model="distil-whisper-large-v3-en", # Required model to use for transcription
                # prompt="Specify context or spelling",  # Optional
                response_format="text",  # Optional
                language="en",  # Optional
                temperature=0.0  # Optional
                )
                
            return transcription