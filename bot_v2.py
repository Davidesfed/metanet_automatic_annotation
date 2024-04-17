import json
from nltk.corpus import framenet as fn
from nltk.tag import pos_tag
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import csv
from nltk.corpus.reader.framenet import FramenetError


# Best-effort identification of (candidate) source and target concepts
# in metaphors extracted from MetaNet Wiki examples,
# based on their conceptual metaphor frames and their LUs

# For each conceptual metaphor m, the src and tgt LUs are looked for following these rules:
# 1) apply retrieve_lus() to src/tgt frame of m
# 2) apply retrieve_lus() to “is subcase of” related frames, starting from src/tgt frames of m
# 3) breadth-first search of "both source and target subcase of" and "src/tgt subcase of" related metaphors:
#    \-> apply rules 1 and 2 to each related metaphor


# given a MetaNet frame, returns the set of its associated Lexical Units
def retrieve_lus(frame):
    lus = set()
    with open("data/metanet_frames.jsonl", encoding="utf-8") as scraped_data:
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
                        pass
                        #print(f"WARNING - MISSING FRAMENET FRAME: {err}")
    
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


# rel_dict is a dict of dicts
# each internal dict contains related nodes and their distance
# the expansion adds to the external dictionary all reachable nodes and their distance
def relation_expansion(rel_dict):
    # for each key
    for cur_node in rel_dict.keys():
        # build a FIFO queue
        # add each node in the main value list to the queue
        queue = list(rel_dict[cur_node].keys())

        # while the queue is not void
        while queue:
            # n = first node in the queue
            # remove n from the queue
            n = queue.pop(0)

            # expand on n if possiblle
            if n in rel_dict.keys():

                # for each node related to n
                for new_node in rel_dict[n].keys():
                    # add it to the queue
                    queue.append(new_node)

                    # if new_node is not in the cur_node related list, add it
                    if new_node not in (rel_dict[cur_node].keys()):
                        # the distance to new_node is (the distance to n) + 1 
                        rel_dict[cur_node][new_node] = rel_dict[cur_node][n] + 1
                    else:
                        # if a shorter path is found, update the distance
                        rel_dict[cur_node][new_node] = min(rel_dict[cur_node][new_node], rel_dict[cur_node][n] + 1)


# auxiliary function to update a candidate concepts distance dictionary
def update_distance_dict(distance_dict, frame, new_distance):
    for lexical_unit in retrieve_lus(frame):
        # if lexical_unit is not in the dict, add it
        if lexical_unit not in distance_dict.keys():
            distance_dict[lexical_unit] = new_distance
        # if a shorter path is found, update the distance
        else:
            distance_dict[lexical_unit] = min(distance_dict[lexical_unit], new_distance)



def main():

    ###########################################
    # Read metanet_classes and metanet_frames #
    ###########################################

    # save source and target of each metaphor in a dictionary
    metaphors_dict = dict()
    # save "source subcase of" and "target subcase of" relations in two dictionaries
    super_src_of = dict()
    super_tgt_of = dict()

    with open("data/metanet_classes.jsonl", encoding="utf-8") as scraped_data:
        for line in scraped_data:
            scraped = json.loads(line.strip())
            
            metaphor = scraped["metaphor"]
            src = scraped["source frame"]
            tgt = scraped["target frame"]
            examples = scraped["examples"]

            metaphors_dict[metaphor] = {"source": src, "target": tgt, "examples": examples}

            super_st = scraped["both s and t subcase of"]

            super_source = scraped["source subcase of"]
            super_src_list = super_st + super_source
            super_src_of[metaphor] = {el: 1 for el in super_src_list}

            super_target = scraped["target subcase of"]
            super_tgt_list = super_st + super_target
            super_tgt_of[metaphor] = {el: 1 for el in super_tgt_list}

    # save relevant_fn_frames for each frame
    fn_frames_for = dict()
    # save "subcase of" frame relation in a dictionary
    super_frames_of = dict()

    with open("data/metanet_frames.jsonl", encoding="utf-8") as scraped_data:
        for line in scraped_data:
            scraped = json.loads(line.strip())
            
            frame = scraped["frame"]
            super_frames = scraped["subcase of"]
            fn = scraped["relevant_fn_frames"]

            super_frames_list = super_frames
            super_frames_of[frame] = {el: 1 for el in super_frames_list}
            fn_frames_for[frame] = fn

    # extend the value lists of the subcase dictionaries with a breadth-first search of the relation
    relation_expansion(super_src_of)
    relation_expansion(super_tgt_of)
    relation_expansion(super_frames_of)
    
    ##########################################################
    # automatically annotate examples using the dictionaries #
    ##########################################################

    with open("data/metanet_bot_v2.tsv", "w", encoding='utf-8', newline="") as  tsvfile:
        output_writer = csv.writer(tsvfile, delimiter='\t', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        output_writer.writerow(["#candidate_src", "#candidate_tgt", "#sentence"])

        lost_count = 0

        # for each conceptual metaphor in MetaNet
        for met in metaphors_dict.keys():

            #######################
            # retrieve source LUs #
            #######################

            # list containing this metaphor and the subsumers found in a breadth-first search of "source subcase of" relations
            met_subsumers_list = [met] + list(super_src_of[met].keys())
            # source concept candidates
            source_lus = dict()

            # RULE 3) apply rules 1 and 2 to each metaphor in met_subsumers_list
            while met_subsumers_list:
                
                # retrieve next metaphor
                cur_met = met_subsumers_list.pop(0)

                # RULE 1) src/tgt frame of cur_met
                if cur_met in metaphors_dict.keys():
                    update_distance_dict(source_lus,
                                         metaphors_dict[cur_met]["source"],
                                         super_src_of[met][cur_met] if cur_met != met else 0)
                
                # RULE 2) breadth-first search of “is subcase of” related frames, starting from src/tgt frame of cur_met
                if cur_met in metaphors_dict.keys():
                    curmet_src = metaphors_dict[cur_met]["source"]

                    if curmet_src in super_frames_of.keys():
                        frame_subsumers_list = list(super_frames_of[curmet_src].keys())
                        while frame_subsumers_list:
                            cur_frame = frame_subsumers_list.pop(0)
                            update_distance_dict(source_lus,
                                                 cur_frame,
                                                 (super_src_of[met][cur_met] if cur_met != met else 0)
                                                  + super_frames_of[curmet_src][cur_frame])

            #######################
            # retrieve target LUs #
            #######################

            # list containing this metaphor and the subsumers found in a breadth-first search of "target subcase of" relations
            met_subsumers_list = [met] + list(super_tgt_of[met].keys())
            # target concept candidates
            target_lus = dict()

            # RULE 3) apply rules 1 and 2 to each metaphor in met_subsumers_list
            while met_subsumers_list:
                
                # retrieve next metaphor
                cur_met = met_subsumers_list.pop(0)

                # RULE 1) src/tgt frame of cur_met
                if cur_met in metaphors_dict.keys():
                    update_distance_dict(target_lus,
                                         metaphors_dict[cur_met]["target"],
                                         super_tgt_of[met][cur_met] if cur_met != met else 0)
                
                # RULE 2) breadth-first search of “is subcase of” related frames, starting from src/tgt frame of cur_met
                if cur_met in metaphors_dict.keys():
                    curmet_tgt = metaphors_dict[cur_met]["target"]

                    if curmet_tgt in super_frames_of.keys():
                        frame_subsumers_list = list(super_frames_of[curmet_tgt].keys())
                        while frame_subsumers_list:
                            cur_frame = frame_subsumers_list.pop(0)
                            update_distance_dict(target_lus,
                                                 cur_frame,
                                                 (super_tgt_of[met][cur_met] if cur_met != met else 0)
                                                  + super_frames_of[curmet_tgt][cur_frame])
            
            #################################
            # build output for each example #
            #################################
            
            for ex in metaphors_dict[met]["examples"]:
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
                        if tagged_lu == token:
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


            '''
            # if there are both some source and some target candidates              
            if source_candidates and target_candidates:
                # build a list of source candidates sorted by relational distance
                source_cand_list = [x[0] for x in sorted(source_candidates.items(), key = lambda kv : kv[1])]
                # build a list of target candidates sorted by relational distance
                target_cand_list = [x[0] for x in sorted(target_candidates.items(), key = lambda kv : kv[1])]

                # output the two candidate concepts lists for met
                output_writer.writerow([json.dumps(source_cand_list), json.dumps(target_cand_list), met])

            # else print a warning
            else:
                lost_count += 1
                print(f"WARNING: Conceptual Metaphor {met} cannot be represented")
            '''




if __name__ == '__main__': main()



