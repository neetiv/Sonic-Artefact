# Imports
import json
import re
import time

from faster_whisper import WhisperModel # for speech processing
from faster_whisper.audio import decode_audio

# Constants & Config
AUDIO_PATH = "data/us_election_2020_2nd_presidential_debate.mp3"
FILTERED_DATA_PATH = "filtered_data.json"
OUTPUT_PATH = "time_windows.json"  # populate time windows where audio must be louder
MODEL_SIZE = "base.en"  # loading base model of whisper
# Start and end times
CLIP_START = 0
CLIP_END = 60  # will eventually replace with audio's real length, set for test runs rn
SAMPLE_RATE = 16000  # whisper model expects 16k Hz, speech
PADDING = 0.05  # padding to boosted windows for smoothness of volume transition

# Cleaning functions, match those in the notebook so the words match filtered words list
# Replace special characters
def clean(text):
    text = re.sub(r"\[[^\]]*\]|\([^)]*\)", " ", text)
    text = text.replace("’", "'").replace("…", " ").lower()
    return re.findall(r"[a-z]+(?:'[a-z]+)?", text)

# Normalize contractions
def norm(w):
    if w.endswith("n't"):
        return "not"
    return re.sub(r"('s|'re|'ve|'ll|'d|'m)$", "", w)

def load_filtered_data(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    words = {entry["text"] for entry in data["words"]}
    phrases = [tuple(entry["text"].split()) for entry in data["phrases"]]
    return words, phrases