import json
import os
import re
import requests
from nltk.corpus import framenet as fn
from nltk.tag import pos_tag
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import csv
from nltk.corpus.reader.framenet import FramenetError
from nltk.corpus import wordnet as wn
from metanet_automatic_annotation import retrieve_manual_annotations

TEST = [
    {
        "category": "WORDS ARE CONTAINERS",
        "sentence": "That remark is completely impenetrable.",
        "source frame": "Containing",
        "target frame": "Word",
        "source": "impenetrable",
        "target": "remark",
        "type": "AN"
    }
]

def main():
    print(wn.synsets("Seeing"))
        


if __name__ == "__main__":
    main()

