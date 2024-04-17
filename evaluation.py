import json
import os

def compute_label(manual_annotation, automatic_annotation):
    label = ""
    label_dict = {
        'source positives': automatic_annotation['source'] != '',
        'source negatives': automatic_annotation['source'] == '',
        'target positives': automatic_annotation['target'] != '',
        'target negatives': automatic_annotation['target'] == '',
        'true source': (automatic_annotation['source'] != '') == (manual_annotation['source'] != ''), # iff implementation
        'false source': (automatic_annotation['source'] != '') == (manual_annotation['source'] == ''),
        'true target': (automatic_annotation['target'] != '') == (manual_annotation['target'] != ''),
        'false target': (automatic_annotation['target'] != '') == (manual_annotation['target'] == ''),
    }
    label_dict = dict(filter(lambda x: x[1], label_dict.items()))
    labels = []
    for key1 in label_dict.keys():
        for key2 in label_dict.keys():
            if key1[-6:] == key2[:6]:
                l = key1.split(' ')
                l.append(key2[7:])
                labels.append(l)
    if labels[0][0] == labels[1][0] and labels[0][2] == labels[1][2]:
        label = " ".join([labels[0][0], labels[0][2]])
    else: 
        label = list(filter(lambda x: 'positives' in x, labels))
        label = " ".join(label[0])
    return label

def update_stats(stats, manual_annotation, automatic_annotation):
    label = compute_label(manual_annotation, automatic_annotation)
    lb = label.replace(' ', '_')
    if label == 'true positives':
        flag = 0
        for cand_source in automatic_annotation["source"].split("/"):
            for cand_target in automatic_annotation["target"].split("/"):
                if manual_annotation["source"] == cand_source and manual_annotation["target"] == cand_target and flag == 0:
                    stats["true positives"]["equal"] += 1
                    flag = 1
                    with open(f'data/results/{lb}_equal.jsonl', 'a', encoding='utf8') as f:
                        f.write(json.dumps(automatic_annotation) + "\n")
        if flag == 0:
            stats["true positives"]["diverse"] += 1
            with open(f'data/results/{lb}_diverse.jsonl', 'a', encoding='utf8') as f:
                f.write(json.dumps(automatic_annotation) + "\n")
    
    else:
        stats[label] += 1
        with open(f'data/results/{lb}.jsonl', 'a', encoding='utf8') as f:
            f.write(json.dumps(automatic_annotation) + "\n")

def print_stats(stats):
    total = stats["true positives"]["total"] + stats["true negatives"] + stats["false positives"] + stats["false negatives"]
    print(f"Number of metaphors analyzed: {total}/{total + stats['skipped']}")
    print(f'Data sources used: {", ".join(stats["data_sources"])}')
    print(f'True positives: {stats["true positives"]["total"]}, of which EQUAL: {stats["true positives"]["equal"]} and DIVERSE: {stats["true positives"]["diverse"]}')
    for key in stats.keys():
        if key not in ['true positives','skipped', 'data_sources']:
            print(f'{key}: {stats[key]}')


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
        'true source positives': 0,
        'true target positives': 0,
        'false source positives': 0,
        'false target positives': 0,
        'skipped': 0,
        'data_sources': ''
    }

    with open('data/metanet_manual_annotations.json', 'r', encoding='utf8') as f:
        manual_annotations = json.load(f)
    with open('data/metanet_automatic_annotation.json', 'r', encoding='utf8') as f:
        automatic_annotations = json.load(f)
        data_sources = automatic_annotations.pop(0)['data_sources']
        
    for key in stats.keys():
        if key not in ['skipped', 'data_sources']:
            name = key.replace(' ', '_')
            print(f"Pulizia file {name}")
            #with open(f'data/results/{name}.jsonl', 'w', encoding='utf8') as f:
                #pass
    
    for manual_annotation in manual_annotations:
        for automatic_annotation in automatic_annotations:
            if manual_annotation['category'] == automatic_annotation['category']:
                stats = update_stats(stats, manual_annotation, automatic_annotation)
                break

            print(f'Error: categories {manual_annotation["category"]} and {automatic_annotation["category"]} do not match')
            continue
        
    print_stats(stats)

if __name__ == "__main__":
    main()