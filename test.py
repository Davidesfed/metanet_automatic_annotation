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

    with open("data/metanet_frames.jsonl", "r", encoding='utf8') as f:
        metanet_frames = [json.loads(line) for line in f.readlines()]

    for metanet_frame in metanet_frames:
        if metanet_frame["frame"] != "Body of water":
            continue
        lexical_units = {
            "frame": metanet_frame["frame"],
            "ancestors": set(),
            "lus": {
                "metanet": [], 
                "framenet": [], 
                "wordnet": [],
                "conceptnet": []
            }
        }

        frame = metanet_frame.copy()
        depth = 1
        ancestors = [(x,depth) for x in metanet_frame["subcase of"]]
        while len(ancestors) > 0:
            ancestor_name, last_depth = ancestors.pop(0)
            if (ancestor_name, last_depth) in lexical_units["ancestors"]:
                continue
            depth = last_depth + 1
            lexical_units["ancestors"].add((ancestor_name, depth))
            for x in metanet_frames:
                if x["frame"] == ancestor_name:
                    frame = x
                    break
            ancestors.extend([(x,depth) for x in frame["subcase of"]])
        lexical_units["ancestors"] = list(lexical_units["ancestors"])
        print(lexical_units)
        break


if __name__ == "__main__":
    main()

