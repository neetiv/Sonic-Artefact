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

# DESIGN CHOICE: adding functions for main functionalities for individualized testing & code readability

# Loads data at path
def load_filtered_data(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    words = {entry["text"] for entry in data["words"]}
    phrases = [tuple(entry["text"].split()) for entry in data["phrases"]]
    return words, phrases

# Loads the clip from start to end endpoints (mostly for testing)
def load_clip(path, start, end):
    audio = decode_audio(path, sampling_rate=SAMPLE_RATE)
    duration = len(audio) / SAMPLE_RATE
    end = duration if end is None else min(end, duration)
    clip = audio[int(start * SAMPLE_RATE):int(end * SAMPLE_RATE)]
    return clip, end

def transcribe_clip(clip, offset):
    # Calling whisper model!
    model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(clip, word_timestamps=True, language="en")

    # Returns tokens, an array storing timestamp of each word or phrase as it is heard
    tokens = []
    for segment in segments:
        for w in segment.words:
            # Clean the words so they are processed correctly
            for t in clean(w.word):
                tokens.append((norm(t), w.start + offset, w.end + offset))
    return tokens

# Find matches between filtered list and what was heard by whisper model
# returns list of dictionaries
def find_matches(tokens, words, phrases):
    texts = [t[0] for t in tokens]
    matches = []

    for phrase in phrases:
        n = len(phrase)
        for i in range(len(texts) - n + 1):
            if tuple(texts[i:i + n]) == phrase:
                matches.append({"start": tokens[i][1],
                                "end": tokens[i + n - 1][2],
                                "text": " ".join(phrase),
                                "kind": "phrase"})

    for word, start, end in tokens:
        if word in words:
            matches.append({"start": start, "end": end, "text": word, "kind": "word"})

    return matches

# Merge heard intervals (literally leetcode Merge Intervals lmao)
def merge_intervals(matches, padding = PADDING):
    intervals = [[m["start"] - padding, m["end"] + padding] for m in matches]
    # Sort by first value in interval!
    intervals.sort(key=lambda x: x[0])

    merged = []
    for start, end in intervals:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([max(start, 0.0), end])
    return merged


# Main function calling all helpers!
def main():
    w, p = load_filtered_data(FILTERED_DATA_PATH)
    clip, clip_e = load_clip(AUDIO_PATH, CLIP_START, CLIP_END)  # later will use clip_e to set clip end

    t0 = time.time()  # current time is intial time
    tokens = transcribe_clip(clip, CLIP_START)
    print(f"transcribed {len(tokens)} words in {time.time() - t0:.1f}s")

    matches = find_matches(tokens, w, p)
    windows = merge_intervals(matches)

    