import json
import csv

BOT_DIR = "data/bot_results"
AUT_ANN_DIR = "data/results"
COMPARE_DIR = "data/compare_results"

def compute_differences(bot_results, aut_results):
    in_bot_not_in_aut = []
    in_aut_not_in_bot = []
    in_both = []
    for bot_result in bot_results:
        found = False
        for aut_result in aut_results:
            if bot_result["sentence"] == aut_result["sentence"]:
                found = True
                in_both.append(bot_result)
                break
        if not found:
            in_bot_not_in_aut.append(bot_result)
    for aut_result in aut_results:
        found = False
        for bot_result in bot_results:
            if bot_result["sentence"] == aut_result["sentence"]:
                found = True
                break
        if not found:
            in_aut_not_in_bot.append(aut_result)
    return in_bot_not_in_aut, in_aut_not_in_bot, in_both

def main():
    filenames_bot = [
        "true_positives_equal.jsonl",
        "true_positives_diverse.jsonl",
        "false_positives.jsonl",
        "true_negatives.jsonl",
        "false_negatives.jsonl"
    ]

    filenames_aut = [
        "true_positives_equal.jsonl",
        "true_positives_diverse.jsonl",
        "true_source_positives.jsonl",
        "true_target_positives.jsonl",
        "false_positives.jsonl",
        "false_source_positives.jsonl",
        "false_target_positives.jsonl",
        "true_negatives.jsonl",
        "false_negatives.jsonl"
    ]

    bot_to_aut_mappings = {
        "true_positives_equal.jsonl": ["true_positives_equal.jsonl"],
        "true_positives_diverse.jsonl": ["true_positives_diverse.jsonl"],
        "false_positives.jsonl": ["false_positives.jsonl"],
        "true_negatives.jsonl": ["true_negatives.jsonl", "false_source_positives.jsonl","false_target_positives.jsonl",],
        "false_negatives.jsonl": ["false_negatives.jsonl", "true_source_positives.jsonl", "true_target_positives.jsonl"]
    }

    for filename in filenames_bot:
        with open(f"{BOT_DIR}/{filename}", "r", encoding='utf8') as f:
            bot_results = [json.loads(line) for line in f]

        aut_results = []
        for aut_filename in bot_to_aut_mappings[filename]:
            with open(f"{AUT_ANN_DIR}/{aut_filename}", "r", encoding='utf8') as f:
                aut_results.extend([json.loads(line) for line in f])
        
        in_bot_not_in_aut,  in_aut_not_in_bot, in_both = compute_differences(bot_results, aut_results)
        stats = {
            "in_bot_not_in_aut": in_bot_not_in_aut,
            "in_aut_not_in_bot": in_aut_not_in_bot,
            "in_both": in_both
        }
        for key in stats.keys():
            with open(f"{COMPARE_DIR}/{key}_{filename[:-1]}", "w", encoding='utf8') as f:
                json.dump(stats[key], f, indent=4)
        
        with open(f"{COMPARE_DIR}/comparison_overview.jsonl", "a", encoding='utf8') as f:
                tmp = {
                    "filename": filename.split(".")[0],
                    "in_bot_not_in_aut": len(in_bot_not_in_aut),
                    "in_aut_not_in_bot": len(in_aut_not_in_bot),
                    "in_both": len(in_both)
                }
                f.write(json.dumps(tmp) + "\n")
                


    
    

if __name__ == "__main__":
    main()