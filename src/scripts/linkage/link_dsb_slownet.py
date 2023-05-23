import pandas as pd
import lxml.etree as lxml
import csv, pickle, time

class Linker:

    def __init__(self):
        self.dsb_df = pd.read_csv('../../../res/dsb_data.csv', delimiter='|', low_memory=False)
        self.slownet = pickle.load(open('../../../res/slownet_extended.graph', 'rb'))

    def get_synset_relations(self, synset_id):
        hypernyms = []
        antonyms = []

        for connection in self.slownet.nodes[synset_id]['connections']:
            if (connection['type'] == 'hypernym'):
                hypernym_synset_id = connection['synset_id']
                hypernyms.extend(self.slownet.nodes[hypernym_synset_id]['slo_literals'])
            if (connection['type'] == 'near_antonym'):
                antonym_synset_id = connection['synset_id']
                antonyms.extend(self.slownet.nodes[antonym_synset_id]['slo_literals'])

        return antonyms, hypernyms
    
    def to_dsb_category(self, synset_category):
        if (synset_category == 'a'):
            return 'adjective'
        elif (synset_category == 'n'):
            return 'noun'
        elif (synset_category == 'v'):
            return 'verb'
        elif (synset_category == 'b'):
            return 'adverb'
        else:
            return None
        
    
    def print_stats(self, match_counter, matched_senses, matched_synsets):
        print('Number of candidate DSB sense comparisons per number of synonym matches:\n', match_counter)
        print('Number of different DSB senses linked: ', len(set(matched_senses)))
        print('Number of different SloWnet synsets linked: ', len(set(matched_synsets)))

    def link_entities(self):
        csv_file = open('../../../res/test_linkage.csv', 'w')
        fieldnames = [
            'dsb_sense_id',
            'slownet_synset_id',
            'matched_category',
            'matched_synonyms',
            'matched_antonyms',
            'matched_hypernyms',
            'dsb_dummy_sense'
        ]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter='|')
        writer.writeheader()

        match_counter = dict()
        matched_senses = []
        matched_synsets = []

        #match_threshold = 1

        # Iterate over synsets in SloWnet
        for synset_id in self.slownet.nodes:
            slo_literals = self.slownet.nodes[synset_id]['slo_literals']
            antonyms, hypernyms = self.get_synset_relations(synset_id)
            category = self.to_dsb_category(synset_id[-1])
            match_threshold = 1 if len(slo_literals) > 1 else 0
            for literal in slo_literals:
                # Iterate over literals in the synset
                synonyms = slo_literals.copy()
                synonyms.remove(literal)

                candidates = self.dsb_df.loc[self.dsb_df['form'] == literal]
                for idx, candidate in candidates.iterrows():
                    # Iterate over dsb candidates with the same form
                    candidate_synonyms = str(candidate['synonyms']).split(';')
                    candidate_antonyms = str(candidate['antonyms']).split(';')
                    candidate_hypernyms = str(candidate['hypernyms']).split(';')
                    candidate_hyponyms = str(candidate['hyponyms']).split(';')

                    if (str(candidate['lexical_unit_type']) == 'single_lexeme_unit'):
                        candidate_category = str(candidate['lexical_unit_category'])
                    else:
                        candidate_category = None

                    try:
                        candidate_position = int(candidate['sense_position'])
                        candidate_dummy = False
                    except ValueError:
                        candidate_dummy = True

                    matching_synonyms = set(synonyms) & set(candidate_synonyms)
                    matching_antonyms = set(antonyms) & set(candidate_antonyms)
                    matching_hypernyms = set(hypernyms) & set(candidate_hypernyms)

                    matched_synonyms = '/'.join(map(str, [len(matching_synonyms), len(synonyms)]))
                    matched_antonyms = '/'.join(map(str, [len(matching_antonyms), len(antonyms)]))
                    matched_hypernyms = '/'.join(map(str, [len(matching_hypernyms), len(hypernyms)]))
                    matched_category = True if category == candidate_category else False

                    if (len(matching_synonyms) in match_counter):
                        match_counter[len(matching_synonyms)] += 1
                    else:
                        match_counter[len(matching_synonyms)] = 1

                    if (
                        (len(matching_synonyms) >= match_threshold or
                        len(matching_antonyms) >= match_threshold or
                        len(matching_hypernyms) >= match_threshold) and
                        matched_category
                        ):
                        row = {
                            'dsb_sense_id': candidate['sense_id'],
                            'slownet_synset_id': synset_id,
                            'matched_category': matched_category,
                            'matched_synonyms': matched_synonyms,
                            'matched_antonyms': matched_antonyms,
                            'matched_hypernyms': matched_hypernyms,
                            'dsb_dummy_sense': candidate_dummy}
                        writer.writerow(row)
                        matched_senses.append(candidate['sense_id'])
                        matched_synsets.append(synset_id)
            
        csv_file.close()
        self.print_stats(match_counter, matched_senses, matched_synsets)
        
def main():
    t1 = time.time()
    linker = Linker()
    linker.link_entities()
    t2 = time.time() - t1
    print('TOTAL TIME ELAPSED: ' + str(t2))

if __name__ == "__main__":
    main()