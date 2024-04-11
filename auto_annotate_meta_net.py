import json
from nltk.corpus import framenet as fn
from nltk.tag import pos_tag
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import csv
from nltk.corpus.reader.framenet import FramenetError


# Best-effort identification of source and target concepts in metaphors
# extracted from MetaNet Wiki examples,
# based on their conceptual metaphor frames and their LUs


def retrieve_lus(frame):
    lus = set()
    with open("lexunits.jsonl", encoding="utf-8") as scraped_data:
        for line in scraped_data:
            scraped = json.loads(line.strip())

            # add all lus in the MetaNet frame page
            if scraped["frame"] == frame:
                lus.update(scraped["lus"])

                # add lus from related FrameNet frames
                for fn_frame in scraped["relevant_fn_frames"]:
                    try:
                        lus.update([lu for lu in fn.frame(fn_frame).lexUnit])
                    except FramenetError as err:
                        print(f"WARNING - MISSING FRAMENET FRAME: {err}")
    
    return lus


def universal_to_wordnet(tagged_sentence):
    wordnet_tokens = []
    for token in tagged_sentence:
        if token[1] == "NOUN":
            wordnet_tokens.append((token[0].lower(), 'n'))
        if token[1] == "ADJ":
            wordnet_tokens.append((token[0].lower(), 'a'))
        if token[1] == "VERB":
            wordnet_tokens.append((token[0].lower(), 'v'))
        if token[1] == "ADV":
            wordnet_tokens.append((token[0].lower(), 'r'))
    
    return wordnet_tokens



def main():
    with open("metaphors.jsonl", encoding="utf-8") as scraped_data:
        with open("metanet_bot.tsv", "w", encoding='utf-8', newline="") as  tsvfile:
            output_writer = csv.writer(tsvfile, delimiter='\t', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            output_writer.writerow(["#candidate_src", "#candidate_tgt", "#sentence"])

            # for each conceptual metaphor in MetaNet
            for line in scraped_data:
                scraped = json.loads(line.strip())
                
                # retrieve source LUs
                source_frame = scraped["source frame"]
                source_lus = retrieve_lus(source_frame)

                # retrieve target LUs
                target_frame = scraped["target frame"]
                target_lus = retrieve_lus(target_frame)
                

                for ex in scraped["examples"]:
                    sentence = ex.strip()

                    tagged = pos_tag(word_tokenize(sentence), tagset='universal')
                    filtered = universal_to_wordnet(tagged)

                    wnl = WordNetLemmatizer()
                    lemmatized = [(wnl.lemmatize(token[0], token[1]), token[1]) for token in filtered]

                    # detect source and target based on LUs
                    candidate_source = set()
                    candidate_target = set()

                    for token in lemmatized:

                        # find source LUs with matching POS
                        for lu in source_lus:
                            tagged_lu = tuple(lu.split("."))
                            if tagged_lu == token:                  #TODO: check
                                candidate_source.add(token[0])
                        # if no match, find source LUs ignoring POS
                        if len(candidate_source) == 0:
                            for lu in source_lus:
                                untagged_lu = lu.split(".")[0]
                                if untagged_lu == token[0]:
                                    candidate_source.add(token[0])

                        # find target LUs with matching POS
                        for lu in target_lus:
                            tagged_lu = tuple(lu.split("."))
                            if tagged_lu == token:
                                candidate_target.add(token[0])
                        # if no match, find target LUs ignoring POS
                        if len(candidate_target) == 0:
                            for lu in target_lus:
                                untagged_lu = lu.split(".")[0]
                                if untagged_lu == token[0]:
                                    candidate_target.add(token[0])

                    output_writer.writerow(["/".join(candidate_source), "/".join(candidate_target), sentence])




if __name__ == '__main__': main()



