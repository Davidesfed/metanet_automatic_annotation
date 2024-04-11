import json
from nltk.corpus import framenet as fn
from nltk.corpus import wordnet as wn
from nltk.corpus.reader.framenet import FramenetError
import requests


def retrieve_lus_from(data_source, automatic_annotation):
    if data_source == "metanet":
        return retrieve_lus_from_metanet(automatic_annotation)
    elif data_source == "framenet":
        return retrieve_lus_from_framenet(automatic_annotation)
    elif data_source == "wordnet":
        return retrieve_lus_from_wordnet(automatic_annotation)
    elif data_source == "conceptnet":
        return retrieve_lus_from_conceptnet(automatic_annotation)

def retrieve_lus_from_metanet(automatic_annotation):
    lexical_units = {"source": set(), "target": set()}
    with open('category_lexical_units.json', 'r', encoding='utf8') as f:
        metaphors = json.load(f)
    for metaphor in metaphors:
        if metaphor["category"] == automatic_annotation["category"]:
            lexical_units["source"] = metaphor["source lus"]
            lexical_units["target"] = metaphor["target lus"]
    return {"source": list(lexical_units["source"]), "target": list(lexical_units["target"])}

def retrieve_lus_from_framenet(automatic_annotation):
    lexical_units = {"source": set(), "target": set()}
    try:
        for key in ["source", "target"]:
            word = automatic_annotation[key + " frame"]
            frame = fn.frame(word)
            for lu in frame.lexUnit:
                lexical_units[key].add(lu.split('.')[0])
    except FramenetError:
        #print(f"Frame {word} not found in FrameNet")
        pass
    return {"source": list(lexical_units["source"]), "target": list(lexical_units["target"])}

def retrieve_lus_from_wordnet(automatic_annotation):
    lexical_units = {"source": set(), "target": set()}
    for key in ["source", "target"]:
        synset = wn.synsets(automatic_annotation[key + " frame"])[0]
        for word in synset.lemmas():
            lexical_units[key].add(word.name().split('.')[0])
    return {"source": list(lexical_units["source"]), "target": list(lexical_units["target"])}

def retrieve_lus_from_conceptnet(automatic_annotation):
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

