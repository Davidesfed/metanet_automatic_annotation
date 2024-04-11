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
from metanet_automatic_annotation_D import retrieve_manual_annotations

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
    manuel_annotations = retrieve_manual_annotations()
    lexical_units = {"source": set(), "target": set()}
    not_found = []
    for automatic_annotation in manuel_annotations:
        try:
            for key in ["source", "target"]:
                word = automatic_annotation[key + " frame"]
                if word is None:
                    continue
                frames = fn.frames_by_lemma(word.lower())
                #print(len(frames))
                if len(frames) == 0:
                    not_found.append(word)
                #for lu in frame.lexUnit:
                #    lexical_units[key].add(lu.split('.')[0])
        except FramenetError:
            not_found.append(word)
    print("Parole non trovate: ", len(not_found))
        


if __name__ == "__main__":
    main()

