import json, threading, time
import numpy as np
import serial # Lets Python talk to the Arduino over USB
import sounddevice as sd # Plays audio through the computer's speakers
import soundfile as sf # Reads audio files into numpy arrays

WAV_FILE = "data/us_election_2020_2nd_presidential_debate_demo.wav" # .wav file with clip we will use for midterm demo
JSON_DATA = "time_windows.json" # JSON file with time windows where audio must be louder
BASE_VOLUME = 0.4 # Base volume for the audio clip

gain = BASE_VOLUME
pos = 0 # Position in the audio clip

with open(JSON_DATA, "r") as f:
    val = json.load(f) # Load the JSON data into a Python dictionary

start_offset = val["clip"][0] # Start time of the clip
windows = [(w["start"] - start_offset, w["end"] - start_offset) for w in val["windows"]]

data, samplerate = sf.read(WAV_FILE) # Read the audio file into a numpy array

#sd.play(data*BASE_VOLUME, samplerate) # Play the audio clip through the computer's speakers
#sd.wait()

# Whether curr is in any of the time windows
def in_window(curr):
    for s, e in windows:
        if s <= curr <= e:
            return True
    return False

def determine_gain(output, frames, time_info, status):
    global gain, pos # makes sure gain and pos from earlier are used
    if status:
        print(status)
    curr = pos / samplerate # Current time in seconds
    if in_window(curr):
        gain = 1.0 # Increase volume to 100% if in a time window
    else:
        gain = BASE_VOLUME # Otherwise, keep it at base volume

    curr_slice = data[pos:pos+frames] * gain

    # Handling case where we are at the end of the audio clip
    if len(curr_slice) < frames:
        output[:len(curr_slice)] = curr_slice
        output[len(curr_slice):] = 0 # Fill the rest with silence
        raise sd.CallbackStop()

    output[:] = curr_slice # Apply the gain to the audio data
    pos += frames # Move the position forward by the number of frames processed

    with sd.OutputStream(samplerate=samplerate, channels=data.shape[1], callback=determine_gain):
        time.sleep(len(data) / samplerate + 1)