import pandas as pd
import lxml.etree as lxml
import csv, pickle, time

class Linker:

    def __init__(self):
        self.dsb_df = pd.read_csv('../../res/dsb_data.csv', delimiter='|', low_memory=False)
        self.slownet = pickle.load(open('../../res/slownet_extended.graph', 'rb'))

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
    
    def print_stats(self, match_counter, matched_senses, matched_synsets):
        print('Number of candidate DSB sense comparisons per number of synonym matches:\n', match_counter)
        print('Number of different DSB senses linked: ', len(set(matched_senses)))
        print('Number of different SloWnet synsets linked: ', len(set(matched_synsets)))

    def link_entities(self):
        csv_file = open('../../res/dsb_slownet_links_2.csv', 'w')
        fieldnames = ['dsb_sense_id', 'slownet_synset_id']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter='|')
        writer.writeheader()

        match_counter = dict()
        matched_senses = []
        matched_synsets = []

        match_threshold = 1
        for synset_id in self.slownet.nodes:
            # Iterate over synsets in SloWnet
            slo_literals = self.slownet.nodes[synset_id]['slo_literals']
            antonyms, hypernyms = self.get_synset_relations(synset_id)
            for literal in slo_literals:
                # Iterate over literals in the synset
                synonyms = slo_literals.copy()
                synonyms.remove(literal)

                candidates = self.dsb_df.loc[self.dsb_df['form'] == literal]
                for idx, candidate in candidates.iterrows():
                    # Iterate over dsb candidates with the same form
                    candidate_synonyms = str(candidate['synonyms']).split(';')
                    matching_synonyms = set(synonyms) & set(candidate_synonyms)
                    if (len(matching_synonyms) in match_counter):
                        match_counter[len(matching_synonyms)] += 1
                    else:
                        match_counter[len(matching_synonyms)] = 1

                    if (len(matching_synonyms) >= match_threshold):
                        row = {'dsb_sense_id': candidate['sense_id'], 'slownet_synset_id': synset_id}
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