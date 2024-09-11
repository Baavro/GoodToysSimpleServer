import os
from http.server import BaseHTTPRequestHandler
from urllib import parse

from models.STT import STTModel
from models.LLM import LLMModel
from models.TTS import TTSModel

from utils.audio import AudioProcessor
import time
from functools import wraps
from datetime import datetime
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

STTModel_Name = 'groq'
LLMModel_Name = 'groq'
TTSModel_Name = 'aura'

def timing_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} executed in {end_time - start_time:.4f} seconds")
        return result
    return wrapper

class SpeechToSpeechHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.whisper_model = STTModel(model=STTModel_Name)
        self.groq_model = LLMModel(model=LLMModel_Name)
        self.styletts_model = TTSModel(model=TTSModel_Name)
        self.audio_processor = AudioProcessor()
        super().__init__(*args, **kwargs)

    @timing_decorator
    def do_POST(self):
        if self.path == '/upload' and self.headers.get('Transfer-Encoding', '').lower() == 'chunked':
            self._handle_upload()
        else:
            self.send_error(404, "Not Found")

    @timing_decorator
    def do_GET(self):
        if self.path.startswith('/audio/'):
            self._serve_audio_file()
        else:
            self.send_error(404, "Not Found")

    @timing_decorator
    def _handle_upload(self):
        # Timing for read_chunked_audio
        start_time = time.time()
        audio_data, sample_rate, bits, channels = self._read_chunked_audio()
        end_time = time.time()
        print(f"_read_chunked_audio executed in {end_time - start_time:.4f} seconds")

        # Timing for save_wav (input)
        start_time = time.time()
        input_filename = self.audio_processor.save_wav(audio_data, sample_rate, bits, channels)
        end_time = time.time()
        print(f"save_wav (input) executed in {end_time - start_time:.4f} seconds")

        # Timing for transcribe
        start_time = time.time()
        transcription = self.whisper_model.transcribe(input_filename)
        end_time = time.time()
        print(f"whisper_model.transcribe executed in {end_time - start_time:.4f} seconds")

        # Timing for generate_response
        start_time = time.time()
        response_text = self.groq_model.generate_response(transcription)
        response_text = response_text.lower()
        print("Pie's Answer in lower: " + response_text)
        end_time = time.time()
        print(f"groq_model.generate_response executed in {end_time - start_time:.4f} seconds")

        # Timing for generate_speech
        start_time = time.time()
        output_audio = self.styletts_model.generate_speech(response_text)
        end_time = time.time()
        print(f"styletts_model.generate_speech executed in {end_time - start_time:.4f} seconds")

        if TTSModel == 'aura':
            timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
            output_filename = f'{timestamp}_{sample_rate}_{bits}_{channels}.wav'   
            with open(output_filename, "wb") as f:
                for data in output_audio.iter_bytes():
                    f.write(data)
            output_audio.close()
        else:
            # Timing for save_wav (output)
            start_time = time.time()
            output_filename = self.audio_processor.save_wav(output_audio, sample_rate, bits, channels)
            end_time = time.time()
            print(f"save_wav (output) executed in {end_time - start_time:.4f} seconds")

        self._send_audio_uri(output_filename)

    @timing_decorator
    def _read_chunked_audio(self):
        data = bytearray()
        sample_rate = int(self.headers.get('x-audio-sample-rates', '16000'))
        bits = int(self.headers.get('x-audio-bits', '16'))
        channels = int(self.headers.get('x-audio-channel', '1'))

        while True:
            chunk_size = self._get_chunk_size()
            if chunk_size == 0:
                break
            chunk_data = self._get_chunk_data(chunk_size)
            data.extend(chunk_data)

        return bytes(data), sample_rate, bits, channels

    def _get_chunk_size(self):
        size_str = b''
        while True:
            char = self.rfile.read(1)
            if char == b'\r':
                self.rfile.read(1)  # Read '\n'
                break
            size_str += char
        return int(size_str, 16)

    def _get_chunk_data(self, size):
        data = self.rfile.read(size)
        self.rfile.read(2)  # Read '\r\n'
        return data

    @timing_decorator
    def _serve_audio_file(self):
        filename = parse.unquote(self.path[7:])
        if not os.path.exists(filename):
            self.send_error(404, "File not found")
            return

        start = time.time()
        self.send_response(200)
        self.send_header('Content-type', 'audio/wav')
        self.end_headers()
        end = time.time()
        print("Setup in secods: " + (str(end-start)))

        start = time.time()
        with open(filename, 'rb') as file:
            self.wfile.write(file.read())
        end = time.time()
        print("Sent file in secods: " + (str(end-start)))

    @timing_decorator
    def _send_audio_uri(self, filename):
        server_ip = self.server.server_address[0]
        server_port = self.server.server_address[1]
        file_path = os.path.abspath(filename)
        uri = f"http://{server_ip}:{server_port}/audio/{parse.quote(os.path.basename(file_path))}"

        self.send_response(200)
        self.send_header("Content-type", "text/plain;charset=utf-8")
        self.end_headers()
        self.wfile.write(uri.encode('utf-8'))



