import json
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import csv
import buildLUs
import os
import pprint

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

def lus_expansion(metanet_frame, metanet_frames, max_depth):
    lus = metanet_frame['lus']
    if max_depth == 0:
        return lus
    for ancestor_name, depth in metanet_frame['ancestors']:
        if depth > max_depth:
            continue
        try:
            ancestor_frame = next(x for x in metanet_frames if x['frame'] == ancestor_name)
        except StopIteration:
            continue
        for key in ancestor_frame['lus'].keys():
            lus[key].extend(ancestor_frame['lus'][key])
    return lus
            
def build_LUs_set(automatic_annotation, max_depth=1):
    # This function will create the data/lexical_units.jsonl file.
    # If that file already exists, it will just read it
    if not os.path.exists("data/lexical_units.jsonl"):
        buildLUs.build_lexical_units_file()

    lexical_units = {
        'source frame': {'metanet': [], 'framenet': [], 'wordnet': [], 'conceptnet': []},
        'target frame': {'metanet': [], 'framenet': [], 'wordnet': [], 'conceptnet': []}
    }
    with open("data/lexical_units.jsonl", "r", encoding='utf8') as f:
        metanet_frames = [json.loads(line) for line in f.readlines()]

    found = 0
    for metanet_frame in metanet_frames:
        if metanet_frame["frame"] == automatic_annotation["source frame"].replace("_", " "):
            lexical_units["source frame"] = lus_expansion(metanet_frame, metanet_frames, max_depth)
            found += 1
        if metanet_frame["frame"] == automatic_annotation["target frame"].replace("_", " "):
            lexical_units["target frame"] = lus_expansion(metanet_frame, metanet_frames, max_depth)
            found += 1
        if found == 2:
            break
                
    return lexical_units

def preprocess_sentence(sentence):
    tokens = word_tokenize(sentence)
    lemmatizer = WordNetLemmatizer()
    lemmas = [lemmatizer.lemmatize(token) for token in tokens]
    prep_sent = []
    for i in range(len(tokens)):
        lemma_pos = lemmas[i].lower()
        tmp = (lemma_pos, tokens[i])
        prep_sent.append(tmp)
    return prep_sent

def find_candidate_annotation(lexical_units, automatic_annotation, data_sources):
    res = {"source": set(), "target": set(), "type": ""}
    sentence = preprocess_sentence(automatic_annotation["sentence"])
    for key in ["source", "target"]:
        for data_source in data_sources:
            for lu in lexical_units[key + " frame"][data_source]:
                for lemma, token in sentence:
                    if lu == lemma:
                        res[key].add(token)
        res[key] = "/".join(res[key])  
    return res

def build_ancestor_list(automatic_annotation, max_depth):
    generalized_annotations = [automatic_annotation]
    #return generalized_annotations
    with open('data/metaphors_ancestor_hierarchy.json', 'r', encoding='utf8') as f:
        metaphors_ancestor_hierarchy = json.load(f)
    for metanet_class in metaphors_ancestor_hierarchy[automatic_annotation["category"]]:
        if max_depth is not None and metanet_class["depth"] > max_depth:
            continue
        generalized_annotation = {
            "category": metanet_class["category"],
            "sentence": automatic_annotation["sentence"],
            "source frame": metanet_class["source frame"],
            "target frame": metanet_class["target frame"],
            "source": "",
            "target": "",
            "type": ""
        }
        generalized_annotations.append(generalized_annotation)
    return generalized_annotations

def annotate_metaphor(metaphor, data_sources, max_depth=None):
    automatic_annotation = {
        "category": metaphor["category"],
        "sentence": metaphor["sentence"],
        "source frame": metaphor["source frame"],
        "target frame": metaphor["target frame"],
        "source": "",
        "target": "",
        "type": ""
    }

    ancestor_metaphors = build_ancestor_list(automatic_annotation, max_depth)
    for ancestor_metaphor in ancestor_metaphors:
        lexical_units = build_LUs_set(ancestor_metaphor)
        candidate = find_candidate_annotation(lexical_units, ancestor_metaphor, data_sources)
        if candidate["source"] != "" and candidate["target"] != "":
            automatic_annotation["source"] = candidate["source"]
            automatic_annotation["target"] = candidate["target"]
            automatic_annotation["type"] = candidate["type"]
            break
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
        with open('data/false_positives.jsonl', 'a', encoding='utf8') as f:
            f.write(json.dumps(automatic_annotation) + "\n")
    
    if manual_annotation["source"] != "" and manual_annotation["target"] != "" and automatic_annotation["source"] == "" and automatic_annotation["target"] == "":
        stats["false negatives"] += 1
    
    return stats

def print_stats(stats):
    total = stats["true positives"]["total"] + stats["true negatives"] + stats["false positives"] + stats["false negatives"]
    print(f"Number of metaphors analyzed: {total}/{total + stats['skipped']}")
    print(f'Data sources used: {", ".join(stats["data_sources"])}')
    print(f'True positives: {stats["true positives"]["total"]}, of which EQUAL: {stats["true positives"]["equal"]} and DIVERSE: {stats["true positives"]["diverse"]}')
    print(f'True negatives: {stats["true negatives"]}')
    print(f'False positives: {stats["false positives"]}')
    print(f'False negatives: {stats["false negatives"]}')

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
    manual_annotations = retrieve_manual_annotations()
    automatic_annotations = []

    with open('data/false_positives.jsonl', 'w', encoding='utf8') as f:
        pass

    for metaphor in manual_annotations:
        #print(f"Analyzing metaphor: {metaphor['category']}")
        if not all([metaphor["source frame"], metaphor["target frame"]]):
            # print("Missing frames for", metaphor["category"])
            stats['skipped'] += 1
            continue
        automatic_annotation = annotate_metaphor(metaphor, stats['data_sources'])
        automatic_annotations.append(automatic_annotation)
        stats = update_stats(stats, metaphor, automatic_annotation)
        
    with open("data/metanet_automatic_annotation.json", "w", encoding='utf8') as f:
        automatic_annotations.insert(0, stats)
        json.dump(automatic_annotations, f, indent=4)

    print_stats(stats)

if __name__ == '__main__': 
    main()



