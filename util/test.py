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
from metanet_automatic_annotation import annotate_metaphor
from metanet_automatic_annotation import update_stats
from metanet_automatic_annotation import print_stats

TEST = [
    {
        "category": "ABILITY TO EVALUATE GOVERNMENT IS ABILITY TO SEE",
        "sentence": "Government transparency enables the public to hold the government accountable for how they spend their money.",
        "source frame": "Seeing",
        "target frame": "Citizen evaluation of government",
        "source": "transparency",
        "target": "Government",
        "type": "NN"
    }
]

def main():

    stats = {
        'true positives': {
            'total': 0,
            'equal': 0,
            'diverse': 0
        },
        'false positives': 0,
        'true negatives': 0,
        'false negatives': 0,
        'skipped': 0,
        'data_sources': ['metanet', 'framenet', 'wordnet', 'conceptnet']
    }
    automatic_annotations = []

    for metaphor in TEST:
        if not all([metaphor["source frame"], metaphor["target frame"]]):
            # print("Missing frames for", metaphor["category"])
            stats['skipped'] += 1
            continue
        automatic_annotation = annotate_metaphor(metaphor, stats['data_sources'])
        automatic_annotations.append(automatic_annotation)
        stats = update_stats(stats, metaphor, automatic_annotation)

    print_stats(stats)


if __name__ == "__main__":
    main()

