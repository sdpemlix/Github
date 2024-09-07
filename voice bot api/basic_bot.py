import threading
import os
import speech_recognition as sr
from apicall import get_groq_response
from gtts import gTTS
from pydub import AudioSegment
import pygame
import pyttsx3
from io import BytesIO
import asyncio

# Initialize pygame mixer
pygame.mixer.init()

def stream_text(text):
    def play_audio():
        # Stop any currently playing music
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        
        # Convert text to speech
        tts = gTTS(text)
        # Save the speech to a BytesIO object
        audio_fp = BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        
        pygame.mixer.music.load(audio_fp, 'mp3')
        pygame.mixer.music.play()
        
        # Wait for the audio to finish playing
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    
    # Start a new thread for playing audio
    threading.Thread(target=play_audio).start()

# Initialize recognizer
recognizer = sr.Recognizer()
recognizer.energy_threshold = 300  # Adjust based on your environment
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 0.5  # Adjust based on your needs
transcriptions = []
# Function to capture and transcribe audio
async def transcribe_audio():
    

    async def recognize_speech(audio):
        try:
            print("Transcribing...")
            text = recognizer.recognize_google(audio)
            print(f"Transcript: {text}")
            transcriptions.append(text)
            response =get_groq_response(text)
            stream_text(response)
            if text.lower() == "exit":
                print("Exiting the script.")
                os._exit(0)
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")

    with sr.Microphone() as source:
        print("Adjusting for ambient noise... Please wait.")
        recognizer.adjust_for_ambient_noise(source)
        while True:
            try:
                print("Listening...")
                audio = recognizer.listen(source)
                await asyncio.create_task(recognize_speech(audio))
            except sr.WaitTimeoutError:
                print("Listening timed out while waiting for phrase to start")

    return transcriptions

# Function to get response from Groq API

if __name__ == "__main__":
    asyncio.run(transcribe_audio())
    print("All Transcriptions:")
    for i, transcription in enumerate(transcriptions, 1):
        print(f"{i}: {transcription}")
