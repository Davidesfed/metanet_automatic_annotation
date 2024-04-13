import json
from nltk.corpus import framenet as fn
from nltk.corpus import wordnet as wn
from nltk.corpus.reader.framenet import FramenetError
import requests
import re
import os

def retrieve_lus_from(data_source, metanet_class, metanet_frames):
    if data_source.lower() == "metanet":
        return retrieve_lus_from_metanet(metanet_class, metanet_frames)
    elif data_source.lower() == "framenet":
        return retrieve_lus_from_framenet(metanet_class, metanet_frames)
    elif data_source.lower() == "wordnet":
        return retrieve_lus_from_wordnet(metanet_class, metanet_frames)
    elif data_source.lower() == "conceptnet":
        return retrieve_lus_from_conceptnet(metanet_class, metanet_frames)

def retrieve_lus_from_metanet(metanet_class, metanet_frames):
    lexical_units = {"source": set(), "target": set()}
    inserted = 0
    for frame in metanet_frames:
        if frame['frame'] == metanet_class["source frame"]:
            no_pos_lus = [re.sub(r'\.(n|r|v|a)', '', x) for x in frame["lus"]]
            lexical_units["source"].update(no_pos_lus)
            inserted += 1
        if frame['frame'] == metanet_class["target frame"]:
            no_pos_lus = [re.sub(r'\.(n|r|v|a)', '', x) for x in frame["lus"]]
            lexical_units["target"].update(no_pos_lus)
            inserted += 1
        if inserted == 2:
            break

    return {"source": list(lexical_units["source"]), "target": list(lexical_units["target"])}

def retrieve_lus_from_framenet(metanet_class, metanet_frames):
    lexical_units = {"source": set(), "target": set()}
    for frame in metanet_frames:
        for key in ["source", "target"]:
            if frame['frame'] == metanet_class[f"{key} frame"]:
                for fn_frame_name in frame['relevant_fn_frames']:
                    try:
                        fn_frame = fn.frame(fn_frame_name)
                        no_pos_lus = [re.sub(r'\.(n|r|v|a)', '', x) for x in fn_frame.lexUnit]
                        lexical_units[key].update(no_pos_lus)
                    except FramenetError:
                        print(f"FrameNet error with frame {fn_frame_name}")
    return {"source": list(lexical_units["source"]), "target": list(lexical_units["target"])}

def retrieve_lus_from_wordnet(automatic_annotation, metanet_frames):
    lexical_units = {"source": set(), "target": set()}
    for key in ["source", "target"]:
        synsets = wn.synsets(automatic_annotation[key + " frame"])
        if len(synsets) != 0:
            for word in synsets[0].lemmas():
                lexical_units[key].add(word.name().split('.')[0])
    return {"source": list(lexical_units["source"]), "target": list(lexical_units["target"])}

def retrieve_lus_from_conceptnet(automatic_annotation, metanet_frames):
    lexical_units = {"source": set(), "target": set()}
    for key in ["source", "target"]:
        lemma = automatic_annotation[key + " frame"].lower()
        lexical_units[key].add(lemma)
        node_id = "/c/en/" + lemma.replace(" ", "_")
        url = f'http://api.conceptnet.io/query?node={node_id}&other=/c/en'
        concepts = requests.get(url).json()
        for edge in concepts["edges"]:
            for k in ['start', 'end']:
                word = edge[k]["@id"].split('/')[3].replace("_", " ")
                lexical_units[key].add(word)
    return {"source": list(lexical_units["source"]), "target": list(lexical_units["target"])}

def build_lexical_units_file():
    with open("data/metanet_classes.jsonl", "r", encoding='utf8') as f:
        metanet_classes = [json.loads(line) for line in f.readlines()]
    with open("data/metanet_frames.jsonl", "r", encoding='utf8') as f:
        metanet_frames = [json.loads(line) for line in f.readlines()]

    if os.path.exists("data/lexical_units.jsonl"):
        with open("data/lexical_units.jsonl", "w", encoding='utf8') as f:
            print("File already exists, overwriting it")

    i = 0
    for metanet_class in metanet_classes:
        print(f'Processing {metanet_class["metaphor"]}, ({i}/{len(metanet_classes)})')
        i += 1
        if not all([metanet_class["source frame"], metanet_class["target frame"]]):
            continue
        lexical_units = {
            "category": metanet_class["metaphor"],
            "source frame": metanet_class["source frame"],
            "target frame": metanet_class["target frame"],
            "lus": {
                "metanet": {
                    "source": [],
                    "target": []
                }, "framenet": {
                    "source": [],
                    "target": []
                }, "wordnet": {
                    "source": [],
                    "target": []
                }, "conceptnet": {
                    "source": [],
                    "target": []
                }
            }
        }

        for data_source in  ["metanet", "framenet", "wordnet", ]:
            lexical_units["lus"][data_source] = retrieve_lus_from(data_source, metanet_class, metanet_frames)
        
        lexical_units["source frame"] = metanet_class["source frame"]
        lexical_units["target frame"] = metanet_class["target frame"]
        with open("data/lexical_units.jsonl", "a", encoding='utf8') as f:
            f.write(json.dumps(lexical_units) + '\n')

def main():
    build_lexical_units_file()
    

if __name__ == "__main__":
    main()