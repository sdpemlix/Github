import webrtcvad
import pyaudio
import numpy as np
from google.cloud import speech

# Set up VAD
vad = webrtcvad.Vad()
vad.set_mode(1)  # Set aggressiveness mode (0-3)

# Capture Audio
def get_audio_stream():
    pa = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16,
                     channels=1,
                     rate=16000,
                     input=True,
                     frames_per_buffer=1024)
    return stream

# Process Audio with VAD
def read_audio(stream, num_frames):
    audio_data = stream.read(num_frames)
    audio_array = np.frombuffer(audio_data, dtype=np.int16)
    return audio_array

def is_speech(audio_chunk, vad):
    return vad.is_speech(audio_chunk.tobytes(), sample_rate=16000)

# Integrate with Speech-to-Text
def transcribe_audio(audio_chunks):
    client = speech.SpeechClient()
    audio = speech.RecognitionAudio(content=b''.join(audio_chunks))
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
    )
    response = client.recognize(config=config, audio=audio)
    for result in response.results:
        print("Transcript: {}".format(result.alternatives[0].transcript))

# Putting It All Together for Real-Time Processing
def main():
    stream = get_audio_stream()
    audio_chunks = []
    try:
        while True:
            audio_chunk = read_audio(stream, 1024)
            if is_speech(audio_chunk, vad):
                audio_chunks.append(audio_chunk.tobytes())
            else:
                if audio_chunks:
                    transcribe_audio(audio_chunks)
                    audio_chunks = []
    except KeyboardInterrupt:
        stream.stop_stream()
        stream.close()

if __name__ == "__main__":
    main()
