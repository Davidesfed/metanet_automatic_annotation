import json
import re

def main():
    with open('../../1 - Dataset building/metanet_classes.jsonl', 'r', encoding='utf8') as categories_file:
        categories = [json.loads(line) for line in categories_file.readlines()]
    with open('../../1 - Dataset building/metanet_frames.jsonl', 'r', encoding='utf8') as frames_file:
        frames = [json.loads(line) for line in frames_file.readlines()]
    
    lexical_units = []
    for category in categories:
        category_lus = {"category": category["metaphor"], "source lus": [], "target lus": [], "source frame": category["source frame"], "target frame": category["target frame"]}
        inserted = 0
        for frame in frames:
            if frame["frame"] == category["source frame"]:
                new_lus = [re.sub(r'\.(n|r|v|a)', '', x) for x in frame["lus"]]
                category_lus["source lus"].extend(new_lus)
                inserted += 1
            if frame["frame"] == category["target frame"]:
                new_lus = [re.sub(r'\.(n|r|v|a)', '', x) for x in frame["lus"]]
                category_lus["target lus"].extend(new_lus)
                inserted += 1
            if inserted == 2:
                break
        lexical_units.append(category_lus)
    
    with open('category_lexical_units.json', 'w', encoding='utf8') as f:
        json.dump(lexical_units, f)


if __name__ == "__main__":
    main()