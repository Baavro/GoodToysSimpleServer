import wave
import numpy as np
from datetime import datetime

class AudioProcessor:
    def save_wav(self, data, sample_rate, bits, channels):
        timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        filename = f'{timestamp}_{sample_rate}_{bits}_{channels}.wav'
        
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(bits // 8)
            wf.setframerate(sample_rate)
            wf.writeframes(data.tobytes() if isinstance(data, np.ndarray) else data)
        
        return filename