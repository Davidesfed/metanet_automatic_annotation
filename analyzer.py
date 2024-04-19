import json

def retrieve_data_from_json(file_path):
    with open(file_path, "r", encoding='utf8') as f:
        data = json.load(f)
    return data

def retrieve_data_from_jsonl(file_path):
    with open(file_path, "r", encoding='utf8') as f:
        data = [json.loads(line.strip()) for line in f.readlines()]
    return data

def transform_data_to_dict(data, key):
    result = {}
    for item in data:
        if key in item.keys():
            result[item[key]] = item
    return result

def retrieve_data(file_path, output_format=list):
    data = None
    if file_path.endswith(".json"):
        data = retrieve_data_from_json(file_path)
    elif file_path.endswith(".jsonl"):
        data = retrieve_data_from_jsonl(file_path)
    
    if type(output_format) == dict:
        data = transform_data_to_dict(data, list(output_format.keys())[0])
    return data

def main():
    in_bot_no_aut = retrieve_data("data/compare_results/in_bot_not_in_aut_true_positives_equal.json")
    # lexical_units = retrieve_data("data/lexical_units.jsonl", output_format={'frame': dict()})
    metanet_classes = retrieve_data("data/metanet_classes.jsonl")
    automatic_annotations = retrieve_data("data/metanet_automatic_annotations.json", output_format={'sentence': dict()})
    manual_annotations = retrieve_data("data/metanet_manual_annotations.json", output_format={'sentence': dict()})
    
    for metaphor in in_bot_no_aut:
        for metanet_class in metanet_classes:
            if " " + metaphor["sentence"] + '\n' in metanet_class["examples"]:
                print("Sentence:", metaphor["sentence"], "\n")

                for key in ["source", "target"]:
                    print(f"Bot {key}:", metaphor[key])
                    # print(f"{key.capitalize()}  frame:", metanet_class[f"{key} frame"])
                    print(f"{key.capitalize()} automatic annotation:", automatic_annotations[metaphor["sentence"]][key])
                    print(f"{key.capitalize()} manual annotation:", manual_annotations[metaphor["sentence"]][key])
                    # print(f"{key.capitalize()} LUs:", lexical_units[metanet_class[f"{key} frame"]]["lus"])
                    print()

                print("-----------------------------------------------------")

if __name__ == "__main__":
    main()