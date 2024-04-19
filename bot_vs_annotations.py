import json
import csv
from nltk.stem import WordNetLemmatizer

EVAL_DIR = "data/bot_results"

def clear_output_files():
    for name in ['true_positives_equal.jsonl', 'true_positives_diverse.jsonl', 
                 'false_positives.jsonl', 'true_negatives.jsonl', 'false_negatives.jsonl']:
        open(f'{EVAL_DIR}/{name}', 'w').close()

def write_to_file(file, sentence, src, tgt):
    with open(f"{EVAL_DIR}/{file}", "a", encoding='utf-8') as f:
        json.dump({"sentence": sentence, "source": src, "target": tgt}, f)
        f.write("\n")

def main():
    # counters for metaphors annotated by either bot or humans
    correct_positives = 0
    wrong_positives = 0
    false_positives = 0
    true_negatives = 0
    false_negatives = 0
    i = 1
    count = 0

    clear_output_files()

    with open("data/metanet_annotation.csv", "r", encoding='utf-8', newline="") as  csvfile:
        csv_reader = csv.reader(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        next(csv_reader, None)  #skip header

        # for each annotated metaphor
        for line in csv_reader:
            i += 1
            sentence = line[1]
            ann_src = line[2]
            ann_tgt = line[3]
            ann_type = line[4]

            if ann_type != '': #else, the metaphor has not been annotated yet
                count += 1
                with open("data/metanet_bot_v2.tsv", "r", encoding='utf-8', newline="") as  tsvfile:
                    found = False
                    pre_total = correct_positives + wrong_positives + false_positives + true_negatives + false_negatives

                    tsv_reader = csv.reader(tsvfile, delimiter='\t', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                    next(tsv_reader, None)  #skip header
                    for row in tsv_reader:
                        bot_src = row[0]
                        bot_tgt = row[1]
                        bot_sentence = row[2]

                        if bot_sentence == sentence and not found: #confront the annotations for the same example
                            found = True
                            ann_yes = ann_type != "-"
                            bot_yes = (bot_src != "") and (bot_tgt != "")
                            if bot_yes:
                                if ann_yes:
                                    #check if the annotations are compatible (correct positive)
                                    src_candidates = bot_src.lower().split("/")
                                    tgt_candidates = bot_tgt.lower().split("/")
                                    ann_src_pos = ann_type[0].lower() if ann_type[0]!= 'D' else 'r' #TODO: more transaparent conversion of pos tags
                                    ann_tgt_pos = ann_type[1].lower() if ann_type[1]!= 'D' else 'r'
                                    wnl = WordNetLemmatizer()
                                    if wnl.lemmatize(ann_src.lower(), ann_src_pos) in src_candidates \
                                                and wnl.lemmatize(ann_tgt.lower(), ann_tgt_pos) in tgt_candidates:
                                        correct_positives += 1
                                        write_to_file("true_positives_equal.jsonl", sentence, bot_src, bot_tgt)
                                    else:
                                        wrong_positives += 1
                                        write_to_file("true_positives_diverse.jsonl", bot_sentence, bot_src, bot_tgt)
                                else:
                                    false_positives += 1
                                    #print(f"FALSE POSITIVE - sentence: \"{bot_sentence}\"; src: \"{bot_src}\"; tgt: \"{bot_tgt}\"")
                                    write_to_file("false_positives.jsonl", bot_sentence, bot_src, bot_tgt)
                            else:
                                if ann_yes:
                                    false_negatives += 1
                                    write_to_file("false_negatives.jsonl", bot_sentence, bot_src, bot_tgt)
                                else:
                                    true_negatives += 1
                                    write_to_file("true_negatives.jsonl", bot_sentence, bot_src, bot_tgt)
                    post_total = correct_positives + wrong_positives + false_positives + true_negatives + false_negatives
                    if post_total != pre_total + 1:
                        print(">>>", pre_total, post_total, sentence)

        print(count)
        total = correct_positives + wrong_positives + false_positives + true_negatives + false_negatives
        print(f"Total annotations checked = {total}")
        total_positives = correct_positives + wrong_positives + false_negatives
        print(f"Total Positives = {total_positives}")
        print(f"Total Negatives = {true_negatives + false_positives}\n")
        
        print(f"Correct Positives = {correct_positives}")
        print(f"Wrong Positives = {wrong_positives}")
        print(f"True Negatives = {true_negatives}")
        print(f"False Positives = {false_positives}")
        print(f"False Negatives = {false_negatives}\n")
        
        print(f"Loss = {1 - (correct_positives + true_negatives) / total :.2%}")
        print(f"Correct positives / positives = {correct_positives / total_positives :.2%}\n")
        with open(f"{EVAL_DIR}/bot_overview.json", "w") as f:
            stats = {
                "total_annotations": total,
                "true positives": {
                    "equal": correct_positives,
                    "diverse": wrong_positives
                },
                "true_negatives": true_negatives,
                "false_positives": false_positives,
                "false_negatives": false_negatives,
            }
            json.dump(stats, f, indent=4)






if __name__ == '__main__': main()



