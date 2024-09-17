import json
import csv

def main():
    result = []
    metanet_classes = dict()
    with open("data/metanet_classes.jsonl", "r", encoding='utf8') as f:
        for line in f.readlines():
            tmp_class = json.loads(line)
            key = tmp_class["metaphor"][:]
            metanet_classes[key] = tmp_class

    with open("data/metanet_annotation.csv", "r", encoding="utf8") as f:
        reader = csv.reader(f)
        header = next(reader)
        for line in reader:
            tmp = {
                "category": line[0],
                "source frame": metanet_classes[line[0]]["source frame"],
                "target frame": metanet_classes[line[0]]["target frame"],
                "sentence": line[1],
                "source": line[2],
                "target": line[3],
                "type": line[4],
                
            }
            result.append(tmp.copy())

    with open("data/metanet_manual_annotations.json", "w", encoding="utf8") as f:
        json.dump(result, f, indent=2)

if __name__ == "__main__":
    main()