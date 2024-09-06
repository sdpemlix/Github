import threading
import os
import speech_recognition as sr
from groq import Groq
from gtts import gTTS
from pydub import AudioSegment
import pygame
import pyttsx3
from io import BytesIO

'''engine = pyttsx3.init()

def SpeakText(command):
    global engine
    # Stop any ongoing speech
    engine.stop()
    
    # Create a new thread for speaking
    def speak():
        engine.say(command)
        engine.runAndWait()
    
    # Start the new thread
    threading.Thread(target=speak).start()'''
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

# Initialize Groq client
api_key = "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"
if not api_key:
    raise ValueError("API key for Groq is not set. Please set the GROQ_API_KEY environment variable.")
client = Groq(api_key=api_key)

# Function to capture and transcribe audio
def transcribe_audio():
    transcriptions = []

    def recognize_speech(audio):
        try:
            print("Transcribing...")
            text = recognizer.recognize_google(audio)
            print(f"Transcript: {text}")
            transcriptions.append(text)
            response = get_groq_response(text)
            stream_text(response)
            #SpeakText(response)
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
                threading.Thread(target=recognize_speech, args=(audio,)).start()
            except sr.WaitTimeoutError:
                print("Listening timed out while waiting for phrase to start")

    return transcriptions

# Function to get response from Groq API
def get_groq_response(text):
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": text,
                },
                {
                    "role": "system",
                    "content": "Please provide a concise, one-line response."
                }
            ],
            model="llama3-8b-8192",
            temperature=1,
            max_tokens=1024,
            top_p=1,
            )
        response = chat_completion.choices[0].message.content
        print(f"Groq Response: {response}")
    except Exception as e:
        print(f"Error getting response from Groq API: {e}")
        response = "Sorry, I couldn't get a response from the server."
    return response

if __name__ == "__main__":
    transcriptions = transcribe_audio()
    print("All Transcriptions:")
    for i, transcription in enumerate(transcriptions, 1):
        print(f"{i}: {transcription}")
