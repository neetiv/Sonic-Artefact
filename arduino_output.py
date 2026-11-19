import json, threading, time
import numpy as np
import serial # Lets Python talk to the Arduino over USB
import sounddevice as sd # Plays audio through the computer's speakers
import soundfile as sf # Reads audio files into numpy arrays

WAV_FILE = "data/us_election_2020_2nd_presidential_debate_demo.wav" # .wav file with clip we will use for midterm demo
JSON_DATA = "time_windows.json" # JSON file with time windows where audio must be louder
BASE_VOLUME = 0.5 # Base volume for the audio clip
PAD = -0.05

gain = BASE_VOLUME
pos = 0 # Position in the audio clip

# Arduino constants
PORT = "/dev/cu.usbserial-10"
SERIAL_SPEED = 9600
volume = 0

with open(JSON_DATA, "r") as f:
    val = json.load(f) # Load the JSON data into a Python dictionary

start_offset = val["clip"][0] # Start time of the clip
windows = [(w["start"] + PAD - start_offset, w["end"] - PAD - start_offset) for w in val["windows"]]

data, samplerate = sf.read(WAV_FILE) # Read the audio file into a numpy array
data = data / np.max(np.abs(data))

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
        gain = BASE_VOLUME + (1.0 - BASE_VOLUME) * volume / 100
    else:
        gain = 0.05 # Otherwise, keep it at base volume

    curr_slice = data[pos:pos+frames] * gain

    # Handling case where we are at the end of the audio clip
    if len(curr_slice) < frames:
        output[:len(curr_slice)] = curr_slice
        output[len(curr_slice):] = 0 # Fill the rest with silence
        raise sd.CallbackStop()

    output[:] = curr_slice # Apply the gain to the audio data
    pos += frames # Move the position forward by the number of frames processed

def read_arduino():
    global volume
    ser = serial.Serial(PORT, SERIAL_SPEED) # Connect to the Arduino
    time.sleep(2) # Wait for the connection to establish
    while True:
        line = ser.readline().decode("utf-8").rstrip()
        if line:
            try:
                volume = int(line) # Read the volume level from the Arduino
                print(f"Volume from Arduino: {volume}")
            except ValueError:
                pass
threading.Thread(target=read_arduino, daemon=True).start() # Start the Arduino reading in a separate thread

with sd.OutputStream(samplerate=samplerate, channels=data.shape[1], callback=determine_gain):
    time.sleep(len(data) / samplerate + 1)