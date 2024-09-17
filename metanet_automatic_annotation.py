import json
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from nltk.stem import WordNetLemmatizer
import csv
import os

MAX_DEPTH_CLASS = 0
MAX_DEPTH_LUS = 1

def retrieve_manual_annotations():
    if os.path.exists("data/metanet_manual_annotations.json"):
        with open('data/metanet_manual_annotations.json', 'r', encoding='utf8') as f:
            manual_annotations = json.load(f)
            return manual_annotations

    manual_annotations = []
    with open('data/metanet_classes.jsonl', 'r', encoding='utf8') as f:
        metanet_classes = [json.loads(line) for line in f.readlines()]
    with open("data/metanet_annotation.csv", "r", encoding='utf8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            annotation = {
                "category": row["Conceptual metaphor"],
                "sentence": row["Sentence"],
                "source": row["Source"],
                "target": row["Target"],
                "type": row["Type"]
            }
            for metanet_class in metanet_classes:
                if annotation["category"] == metanet_class["metaphor"]:
                    annotation["source frame"] = metanet_class["source frame"]
                    annotation["target frame"] = metanet_class["target frame"]
            manual_annotations.append(annotation)

    with open("data/metanet_manual_annotations.json", "w", encoding='utf8') as f:
        json.dump(manual_annotations, f, indent=4)
    
    return manual_annotations

def lus_expansion(metanet_frame, metanet_frames):
    lus = metanet_frame['lus']
    if MAX_DEPTH_LUS == 0:
        return lus
    for ancestor_name, depth in metanet_frame['ancestors']:
        if depth > MAX_DEPTH_LUS:
            continue
        try:
            ancestor_frame = next(x for x in metanet_frames if x['frame'] == ancestor_name)
        except StopIteration:
            continue
        for key in ancestor_frame['lus'].keys():
            lus[key].extend(ancestor_frame['lus'][key])
    return lus
            
def build_LUs_set(automatic_annotation):
    lexical_units = {
        'source frame': {'metanet': [], 'framenet': [], 'wordnet': [], 'conceptnet': []},
        'target frame': {'metanet': [], 'framenet': [], 'wordnet': [], 'conceptnet': []}
    }
    with open("data/lexical_units.jsonl", "r", encoding='utf8') as f:
        metanet_frames = [json.loads(line) for line in f.readlines()]

    found = 0
    for metanet_frame in metanet_frames:
        if metanet_frame["frame"] == automatic_annotation["source frame"].replace("_", " "):
            lexical_units["source frame"] = lus_expansion(metanet_frame, metanet_frames)
            found += 1
        if metanet_frame["frame"] == automatic_annotation["target frame"].replace("_", " "):
            lexical_units["target frame"] = lus_expansion(metanet_frame, metanet_frames)
            found += 1
        if found == 2:
            break
                
    return lexical_units

def universal_to_wordnet(tagged_sentence):
    wordnet_tokens = []
    for token in tagged_sentence:
        if token[1] == "NOUN":
            wordnet_tokens.append((token[0].lower(), 'n'))
        if token[1] == "ADJ":
            wordnet_tokens.append((token[0].lower(), 'a'))
        if token[1] == "VERB":
            wordnet_tokens.append((token[0].lower(), 'v'))
        if token[1] == "ADV":
            wordnet_tokens.append((token[0].lower(), 'r'))
        if token[1] not in ["NOUN", "ADJ", "VERB", "ADV"]:
            wordnet_tokens.append((token[0].lower(), ''))
    
    return wordnet_tokens

def preprocess_sentence(sentence):
    tokens = word_tokenize(sentence)
    lemmatizer = WordNetLemmatizer()
    pos_tags = pos_tag(tokens, tagset='universal')
    pos_tags = universal_to_wordnet(pos_tags)
    prep_sent = []
    for token, pos in pos_tags:
        if pos == '':
            prep_sent.append(('-', token))
        else:
            prep_sent.append((lemmatizer.lemmatize(token, pos), token))
    #print("Lemmas: ", prep_sent)
    return prep_sent

def find_candidate_annotation(lexical_units, sentence, data_sources):
    res = {"source": set(), "target": set(), "type": ""}
    for key in ["source", "target"]:
        for data_source in data_sources:
            # print(f"LUs of {data_source}: ", lexical_units[key + " frame"][data_source])
            for lu in lexical_units[key + " frame"][data_source]:
                for lemma, token in sentence:
                    if lu == lemma:
                        res[key].add(token)
    return res

def build_ancestor_list(automatic_annotation):
    ancestor_list = [automatic_annotation]
    if MAX_DEPTH_CLASS == 0:
        return ancestor_list
    with open('data/metaphor_ancestors.json', 'r', encoding='utf8') as f:
        metaphor_ancestors = json.load(f)
    for ancestor_class in metaphor_ancestors[automatic_annotation["category"]]:
        if ancestor_class["depth"] > MAX_DEPTH_CLASS:
            continue
        ancestor = {
            "category": ancestor_class["category"],
            "sentence": automatic_annotation["sentence"],
            "source frame": ancestor_class["source frame"],
            "target frame": ancestor_class["target frame"],
            "source": "",
            "target": "",
            "type": ""
        }
        ancestor_list.append(ancestor)
    return ancestor_list

def elect_annotation(automatic_annotation, candidate):
    if len(candidate["source"]) > 0:
        automatic_annotation["source"].update(candidate["source"])
    if len(candidate["target"]) > 0:
        automatic_annotation["target"].update(candidate["target"])
    return automatic_annotation

def annotate_metaphor(metaphor, data_sources):
    automatic_annotation = {
        "category": metaphor["category"],
        "sentence": metaphor["sentence"],
        "source frame": metaphor["source frame"],
        "target frame": metaphor["target frame"],
        "source": set(),
        "target": set(),
        "type": ""
    }
    
    prep_sentence = preprocess_sentence(metaphor["sentence"])
    ancestor_metaphors = build_ancestor_list(automatic_annotation)
    count = 0
    for ancestor_metaphor in ancestor_metaphors:
        if ancestor_metaphor["source frame"] is None or ancestor_metaphor["target frame"] is None:
            count += 1
            continue
        lexical_units = build_LUs_set(ancestor_metaphor)
        candidate = find_candidate_annotation(lexical_units, prep_sentence, data_sources)
        automatic_annotation = elect_annotation(automatic_annotation, candidate)
    automatic_annotation["source"] = "/".join(automatic_annotation["source"]) if count < len(ancestor_metaphors) else None
    automatic_annotation["target"] = "/".join(automatic_annotation["target"]) if count < len(ancestor_metaphors) else None
    return automatic_annotation

def main():
    manual_annotations = retrieve_manual_annotations()
    automatic_annotations = []
    data_sources = ['metanet', 'framenet', 'wordnet', 'conceptnet']

    for i, metaphor in enumerate(manual_annotations):
        if i%50 == 0:
            print('Progress:', i, '/', len(manual_annotations))
        automatic_annotation = annotate_metaphor(metaphor, data_sources)
        automatic_annotations.append(automatic_annotation)
        
    with open("data/metanet_automatic_annotations.json", "w", encoding='utf8') as f:
        automatic_annotations.insert(0, {'data_sources': data_sources})
        json.dump(automatic_annotations, f, indent=4)
        print("Automatic annotations saved in data/metanet_automatic_annotation.json")

if __name__ == '__main__': 
    main()



