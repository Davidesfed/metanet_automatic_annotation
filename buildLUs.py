import json
from nltk.corpus import framenet as fn
from nltk.corpus import wordnet as wn
from nltk.corpus.reader.framenet import FramenetError
import requests
import re
import os

def retrieve_lus_from(data_source, metanet_frame):
    if data_source.lower() == "metanet":
        return retrieve_lus_from_metanet(metanet_frame)
    elif data_source.lower() == "framenet":
        return retrieve_lus_from_framenet(metanet_frame)
    elif data_source.lower() == "wordnet":
        return retrieve_lus_from_wordnet(metanet_frame)
    elif data_source.lower() == "conceptnet":
        return retrieve_lus_from_conceptnet(metanet_frame)

def retrieve_lus_from_metanet(metanet_frame):
    lexical_units = [re.sub(r'\.(n|r|v|a)', '', x) for x in metanet_frame["lus"]]
    return lexical_units

def retrieve_lus_from_framenet(metanet_frame):
    lexical_units = set()
    for fn_frame_name in metanet_frame['relevant_fn_frames']:
        try:
            fn_frame = fn.frame(fn_frame_name)
            no_pos_lus = [re.sub(r'\.(n|r|v|a)', '', x) for x in fn_frame.lexUnit]
            lexical_units.update(no_pos_lus)
        except FramenetError:
            print(f"FrameNet error with frame {fn_frame_name}")
    return list(lexical_units)

def retrieve_lus_from_wordnet(metanet_frame):
    lexical_units = set()
    synsets = wn.synsets(metanet_frame["frame"])
    if len(synsets) != 0:
        for word in synsets[0].lemmas():
            lexical_units.add(word.name().split('.')[0])
    return list(lexical_units)

def retrieve_lus_from_conceptnet(metanet_frame):
    lexical_units = set()
    lemma = metanet_frame["frame"].lower()
    node_id = "/c/en/" + lemma.replace(" ", "_")
    url = f'http://api.conceptnet.io/query?node={node_id}&other=/c/en'
    concepts = requests.get(url).json()
    for edge in concepts["edges"]:
        for key in ['start', 'end']:
            word = edge[key]["@id"].split('/')[3].replace("_", " ")
            lexical_units.add(word)
    return list(lexical_units)

def build_lexical_units_file():
    with open("data/metanet_frames.jsonl", "r", encoding='utf8') as f:
        metanet_frames = [json.loads(line) for line in f.readlines()]

    if os.path.exists("data/lexical_units.jsonl"):
        with open("data/lexical_units.jsonl", "w", encoding='utf8') as f:
            print("File already exists, overwriting it")

    i = 0
    n = len(metanet_frames)
    for metanet_frame in metanet_frames:
        print(f'Processing {metanet_frame["frame"]}, ({i}/{n})')
        i += 1
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

        for data_source in  ["metanet", "framenet", "wordnet",]:
            lexical_units["lus"][data_source] = retrieve_lus_from(data_source, metanet_frame)
        
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

        with open("data/lexical_units.jsonl", "a", encoding='utf8') as f:
            f.write(json.dumps(lexical_units) + '\n')

def main():
    build_lexical_units_file()
    

if __name__ == "__main__":
    main()