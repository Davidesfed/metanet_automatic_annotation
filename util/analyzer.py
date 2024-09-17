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

def compute_label(automatic_srctgt, manual_srctgt):
    if automatic_srctgt is None:
        return "skipped"
    
    if automatic_srctgt == "": 
        if manual_srctgt == "":
            return "true negatives"
        else:
            return "false negatives"
        
    candidates = automatic_srctgt.split("/")
    for candidate in candidates:
        if candidate in manual_srctgt:
            return "true positives"
    return "false positives"

def build_used_frames_dict(metanet_frames, metanet_classes, automatic_annotations, manual_annotations):
    used_frames_dict = dict()

    for frame_name in metanet_frames:
        used_frames_dict[frame_name] = {
                'total': 0,
                'true positives': 0,
                'true negatives': 0,
                'false positives': 0,
                'false negatives': 0,
                'skipped': 0,
        }
        for metanet_class in metanet_classes:
            for key in ["source", "target"]:
                if frame_name == metanet_class[key + " frame"]:
                    for example in metanet_class["examples"]:
                        sentence = example[1:-1]
                        if len(sentence) == 0:
                            continue
                        used_frames_dict[frame_name]['total'] += 1
                        label = compute_label(automatic_annotations[sentence][key], manual_annotations[sentence][key])
                        used_frames_dict[frame_name][label] += 1
        #used_frames_dict[frame_name] = {k: v for k, v in used_frames_dict[frame_name].items() if v != 0}
    used_frames_dict = dict(filter(lambda x: x[1]['total'] != 0, used_frames_dict.items()))
    return used_frames_dict

def build_classification_dict(metanet_frames, metanet_classes):
    used = []
    used_as_ancestor = set()
    not_used = []
    inexistent_ancestor = set()

    for frame_name in metanet_frames:
            
        ancestors = [x[0] for x in metanet_frames[frame_name]['ancestors']]
        for anc in ancestors:
            if anc not in metanet_frames.keys():
                inexistent_ancestor.add(anc)
            else:
                used_as_ancestor.add(anc)

        for metanet_class in metanet_classes:
            if len(metanet_class["examples"]) == 0:
                continue
            if frame_name in [metanet_class["source frame"], metanet_class["target frame"]]:
                used.append(frame_name)
                break

        if frame_name not in used:
            not_used.append(frame_name)

    used_as_ancestor = list(filter(lambda x: x not in used, used_as_ancestor))
    not_used = list(filter(lambda x: x not in used_as_ancestor, not_used))
    classification_dict = {
        'used': {'number': len(used), 'list': used},
        'used_as_ancestor': {'number': len(used_as_ancestor), 'list': used_as_ancestor},
        'not_used': {'number': len(not_used), 'list': not_used},
        'inexistent_ancestor': {'number': len(inexistent_ancestor), 'list': list(inexistent_ancestor)},
    }
    return classification_dict

def frames_info():
    automatic_annotations = retrieve_data("../data/metanet_automatic_annotations.json", output_format={'sentence': dict()})
    manual_annotations = retrieve_data("../data/metanet_manual_annotations.json", output_format={'sentence': dict()})

    metanet_classes = retrieve_data("../data/metanet_classes.jsonl")
    metanet_frames = retrieve_data("../data/lexical_units.jsonl", output_format={'frame': dict()})
                        
    classification_dict = build_classification_dict(metanet_frames, metanet_classes)
    used_frames_dict = build_used_frames_dict(metanet_frames, metanet_classes, automatic_annotations, manual_annotations)

    return classification_dict, used_frames_dict

def metaphor_analysis():
    lexical_units = retrieve_data("../data/lexical_units.jsonl", output_format={'frame': dict()})
    metanet_classes = retrieve_data("../data/metanet_classes.jsonl")
    
    open("analyzer_output.txt", "w").close()

    result_dict = dict()
    for metanet_class in metanet_classes:
        result = ''
        if metanet_class["source frame"] in lexical_units.keys():
            source_lus = lexical_units[metanet_class["source frame"]]["lus"]
        else:
            source_lus = {"metanet": [], "framenet": []}
        if metanet_class["target frame"] in lexical_units.keys():
            target_lus = lexical_units[metanet_class["target frame"]]["lus"]
        else:
            target_lus = {"metanet": [], "framenet": []}
        result_dict[metanet_class["metaphor"]] = {
            'count': 0,
            'total': len(metanet_class["examples"]),
            'source frame': metanet_class["source frame"],
            'source lus': source_lus,
            'target frame': metanet_class["target frame"],
            'target lus': target_lus,
        }
        for i, metaphor in enumerate(false_negatives):
            if " " + metaphor["sentence"] + '\n' in metanet_class["examples"]:
                # result += f'{i+1}. {metaphor["sentence"]}\n'
                result_dict[metanet_class["metaphor"]]['count'] += 1

                '''for key in ["source", "target"]:
                    # print(f"Bot {key}:", metaphor[key])
                    result += f"{key.capitalize()}  frame: {metanet_class[key+' frame']}\n"
                    # result += f"{key.capitalize()} automatic annotation: {automatic_annotations[metaphor['sentence']][key]}\n"
                    result += f"{key.capitalize()} manual annotation: {manual_annotations[metaphor['sentence']][key]}\n"
                    # print(f"{key.capitalize()} LUs:", lexical_units[metanet_class[f"{key} frame"]]["lus"])
                    result += "\n"
                result += "-----------------------------------------------------\n"'''
    
    result_dict = {k: v for k, v in result_dict.items() if v['count'] != 0}
    for i, (key, value) in enumerate(result_dict.items()):
        result = f'{i+1}. Metaphor: {key}\n'
        result += f'Number of FN/Total examples: {value["count"]}/{value["total"]}\n\n'

        result += f'Source frame: {value["source frame"]}\n'
        result += f'Metanet source LUs: {value["source lus"]["metanet"]}\n'
        result += f'Framenet source LUs: {value["source lus"]["framenet"]}\n\n'

        result += f'Target frame: {value["target frame"]}\n'
        result += f'Metanet target LUs: {value["target lus"]["metanet"]}\n'
        result += f'Framenet target LUs: {value["target lus"]["framenet"]}\n\n'
        with open("analyzer_output.txt", "a", encoding='utf8') as f:
            f.write(result)

def results_analysis():
    true_source_positives = retrieve_data("../data/aut_results/true_source_positives.jsonl")
    true_target_positives = retrieve_data("../data/aut_results/true_target_positives.jsonl")

    automatic_annotations = retrieve_data("../data/metanet_automatic_annotations.json", output_format={'sentence': dict()})
    manual_annotations = retrieve_data("../data/metanet_manual_annotations.json", output_format={'sentence': dict()})

    def is_equal(true_one_positive):
        manual_annotation = manual_annotations[true_one_positive["sentence"]]
        for cand_source in true_one_positive["source"].split("/"):
            for cand_target in true_one_positive["target"].split("/"):
                if cand_source in manual_annotation["source"].lower():
                    return "source"
                if cand_target in manual_annotation["target"].lower():
                    return "target"
        return False

    def process_one(true_one_positives):
        result = ''
        n_equal, n_diverse = [0, 0]
        for i, true_one_positive in enumerate(true_one_positives):
            result += f"{i+1}. {true_one_positive['sentence']}\n"
            result += f"Metaphor: {true_one_positive['category']}\n"
            source_or_target = is_equal(true_one_positive)            
            for key in ['source', 'target']:
                result += f"\n{key.capitalize()} frame: {true_one_positive[key + ' frame']}\n"
                if key == source_or_target:
                    n_equal += 1
                    result += f"{key.capitalize()} annotation: {automatic_annotations[true_one_positive['sentence']][key]}\n"
                else:
                    n_diverse += 1
                    result += f"{key.capitalize()} automatic annotation: {automatic_annotations[true_one_positive['sentence']][key]}\n"
                    result += f"{key.capitalize()} manual annotation: {manual_annotations[true_one_positive['sentence']][key]}\n"
            result += "-----------------------------------------------------\n"
        result = f"Equal: {n_equal} Diverse: {n_diverse}\n\n" + result
        return result
    
    open("analyzer_output.txt", "w").close()
    res_source = process_one(true_source_positives)
    #res_target = process_one(true_target_positives)

    with open("analyzer_output.txt", "a", encoding='utf8') as f:
        f.write(res_source)
        #f.write(res_target)
    
def main():
    #results_analysis()
    classification_dict, used_frames_dict = frames_info()
    with open("../metanet_evaluation/frame_classification.json", "w", encoding='utf8') as f:
        
        json.dump(classification_dict, f, indent=4)
    with open("../metanet_evaluation/used_frame.json", "w", encoding='utf8') as f:
        json.dump(used_frames_dict, f, indent=4)

if __name__ == "__main__":
    main()