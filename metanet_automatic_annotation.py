import json
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import csv
import buildLUs
import os

def retrieve_manual_annotations():
    if os.path.exists("data/metanet_manual_annotations.json"):
        with open('data/metanet_manual_annotations.json', 'r', encoding='utf8') as f:
            manual_annotations = json.load(f)
            return manual_annotations

    manual_annotations = []
    with open('data/category_lexical_units.json', 'r', encoding='utf8') as f:
        metaphors = json.load(f)
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
            for metaphor in metaphors:
                if annotation["category"] == metaphor["category"]:
                    annotation["source frame"] = metaphor["source frame"]
                    annotation["target frame"] = metaphor["target frame"]
            manual_annotations.append(annotation)

    with open("data/metanet_manual_annotation.json", "w", encoding='utf8') as f:
        json.dump(manual_annotations, f, indent=4)
    
    return manual_annotations

def build_LUs_set(automatic_annotation):
    # This function will create the data/lexical_units.jsonl file.
    # If that file already exists, it will just read it
    if not os.path.exists("data/lexical_units.jsonl"):
        buildLUs.build_lexical_units_file()

    with open("data/lexical_units.jsonl", "r", encoding='utf8') as f:
        for line in f:
            lus = json.loads(line.strip())
            if lus["category"] == automatic_annotation["category"]:
                #print("Lexical units already built")
                return lus

def preprocess_sentence(sentence):
    tokens = word_tokenize(sentence)
    lemmatizer = WordNetLemmatizer()
    lemmas = [lemmatizer.lemmatize(token) for token in tokens]
    # pos_tags = pos_tag(tokens)
    prep_sent = []
    for i in range(len(tokens)):
        #new_tag = convert_tag(pos_tags[i][1])
        #if new_tag == '':
        #    continue
        #lemma_pos = lemmas[i].lower() + '.' + new_tag
        lemma_pos = lemmas[i].lower()
        tmp = (lemma_pos, tokens[i])
        prep_sent.append(tmp)
    return prep_sent

def convert_tag(tag):
    if tag.startswith("NN"):
        return 'n'
    elif tag.startswith("JJ"):
        return 'a'
    elif tag.startswith("VB"):
        return 'v'
    elif tag.startswith("RB"):
        return 'r'
    else:
        return ''

def find_candidate_annotation(lexical_units, automatic_annotation):
    res = {"source": set(), "target": set(), "type": ""}
    sentence = preprocess_sentence(automatic_annotation["sentence"])
    for data_source in ["framenet", "wordnet", "conceptnet", "metanet"]:
        for source in lexical_units["lus"][data_source]["source"]:
            for target in lexical_units["lus"][data_source]["target"]:
                for lemma_pos, token in sentence:
                    if source == lemma_pos:
                        res["source"].add(token)
                    if target == lemma_pos:
                        res["target"].add(token)
    return {"source": "/".join(res["source"]), "target": "/".join(res["target"]), "type": ""}

def annotate_metaphor(metaphor):
    automatic_annotation = {
        "category": metaphor["category"],
        "sentence": metaphor["sentence"],
        "source frame": metaphor["source frame"],
        "target frame": metaphor["target frame"],
        "source": "",
        "target": "",
        "type": ""
    }
    lexical_units = build_LUs_set(automatic_annotation)
    candidate = find_candidate_annotation(lexical_units, automatic_annotation)
    if candidate["source"] != "" and candidate["target"] != "":
        automatic_annotation["source"] = candidate["source"]
        automatic_annotation["target"] = candidate["target"]
        automatic_annotation["type"] = candidate["type"]
    return automatic_annotation

def update_stats(stats, manual_annotation, automatic_annotation):
    if all([manual_annotation["source"], automatic_annotation["source"], manual_annotation["target"], automatic_annotation["target"]]):
        stats["true positives"]["total"] += 1
        flag = 0
        for cand_source in automatic_annotation["source"].split("/"):
            for cand_target in automatic_annotation["target"].split("/"):
                if manual_annotation["source"] == cand_source and manual_annotation["target"] == cand_target and flag == 0:
                    stats["true positives"]["equal"] += 1
                    flag = 1
        if flag == 0:
            stats["true positives"]["diverse"] += 1
        
    
    if not any([manual_annotation["source"], automatic_annotation["source"], manual_annotation["target"], automatic_annotation["target"]]):
        stats["true negatives"] += 1
    
    # Da qui sicuramente MAN e AUT hanno prodotto annotazioni diverse
    if manual_annotation["source"] == "" and manual_annotation["target"] == "" and automatic_annotation["source"] != "" and automatic_annotation["target"] != "":
        stats["false positives"] += 1
        print(manual_annotation, automatic_annotation)
    
    if manual_annotation["source"] != "" and manual_annotation["target"] != "" and automatic_annotation["source"] == "" and automatic_annotation["target"] == "":
        stats["false negatives"] += 1
    
    return stats

def print_stats(stats):
    total = stats["true positives"]["total"] + stats["true negatives"] + stats["false positives"] + stats["false negatives"]
    print("Number of metaphors analyzed: ", total)
    print(stats)

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
        'skipped': 0
    }
    manual_annotations = retrieve_manual_annotations()
    automatic_annotations = []

    for metaphor in manual_annotations:
        if not all([metaphor["source frame"], metaphor["target frame"]]):
            # print("Missing frames for", metaphor["category"])
            stats['skipped'] += 1
            continue
        automatic_annotation = annotate_metaphor(metaphor)
        automatic_annotations.append(automatic_annotation)
        stats = update_stats(stats, metaphor, automatic_annotation)
        
    with open("metanet_automatic_annotation_D.json", "w", encoding='utf8') as f:
        automatic_annotations.insert(0, stats)
        json.dump(automatic_annotations, f, indent=4)

    print_stats(stats)

if __name__ == '__main__': 
    main()



