import json, threading, time
import numpy as np
import serial # Lets Python talk to the Arduino over USB
import sounddevice as sd # Plays audio through the computer's speakers
import soundfile as sf # Reads audio files into numpy arrays

WAV_FILE = "data/us_election_2020_2nd_presidential_debate_demo.wav" # .wav file with clip we will use for midterm demo
JSON_DATA = "time_windows.json" # JSON file with time windows where audio must be louder
BASE_VOLUME = 0.3 # Base volume for the audio clip

with open(JSON_DATA, "r") as f:
    val = json.load(f) # Load the JSON data into a Python dictionary

start_offset = val["clip"][0] # Start time of the clip
windows = [(w["start"] - start_offset, w["end"] - start_offset) for w in val["windows"]]
