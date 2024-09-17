import json

_INPUT_FILE = "data/metanet_classes.jsonl"
_OUTPUT_FILE = "data/metaphor_ancestors.json"

def get_parents_of_class(metanet_class):
    ancestors = []
    keys = ["both s and t subcase of", "source subcase of", "target subcase of"]
    for key in keys:
        ancestors.extend(metanet_class[key])
    return ancestors

def build_parent_dicts(metanet_class, metanet_classes, depth):
    ancestors = []
    for parent_category in get_parents_of_class(metanet_class):
        if parent_category not in metanet_classes.keys():
            continue
        parent_class = metanet_classes[parent_category]
        ancestors.append({
            "category": parent_category,
            "depth": depth,
            "source frame": parent_class["source frame"],
            "target frame": parent_class["target frame"]
        })
    return ancestors

def build_ancestors_file():
    metanet_classes = dict()
    with open(_INPUT_FILE, "r", encoding='utf8') as f:
        for line in f.readlines():
            tmp_class = json.loads(line)
            key = tmp_class["metaphor"][:]
            metanet_classes[key] = tmp_class

    keys = ["both s and t subcase of", "source subcase of", "target subcase of"]

    metaphors_ancestor_hierarchy = dict()
    for metanet_class in metanet_classes.values():
        # Inizializzazione della lista di esplorazione degli antenati
        depth = 1
        ancestors = build_parent_dicts(metanet_class, metanet_classes, depth)

        # Inizializzazione dell'oggetto da ritornare
        mn_class = metanet_class.copy()
        mn_class["ancestors"] = []
        for key in keys:
            del mn_class[key]

        # Esplorazione degli antenati e popolamento di mn_class["ancestors"]
        while len(ancestors) > 0:
            ancestor_dict = ancestors.pop(0)
            if ancestor_dict["category"] in [anc["category"] for anc in mn_class["ancestors"]]:
                continue
            mn_class["ancestors"].append(ancestor_dict)
            if ancestor_dict["category"] not in metanet_classes.keys():
                continue
            depth = ancestor_dict["depth"] + 1
            ancestor_class = metanet_classes[ancestor_dict["category"]]
            ancestors.extend(build_parent_dicts(ancestor_class, metanet_classes, depth))
        metaphors_ancestor_hierarchy[mn_class["metaphor"]] = mn_class["ancestors"]

    with open(_OUTPUT_FILE, "w", encoding='utf8') as f:
        f.write(json.dumps(metaphors_ancestor_hierarchy, indent=4))
        print("File saved")

def main():
    build_ancestors_file()

if __name__ == "__main__":
    main()