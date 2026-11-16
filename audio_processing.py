# Imports
from faster_whisper import WhisperModel # for speech processing

import nltk # for list of stopwords
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

from collections import Counter # special map built for counting
import csv # to read dataset

# Opening & reading csv file
with open("data/us_election_2020_2nd_presidential_debate.csv", newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        speaker = row["speaker"]
        text = row["text"]
