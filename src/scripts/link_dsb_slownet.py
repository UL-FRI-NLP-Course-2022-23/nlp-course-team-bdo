import pandas as pd
import lxml.etree as lxml
import csv, pickle, time

class Linker:

    def __init__(self):
        self.dsb_df = pd.read_csv('../../res/dsb_data.csv', delimiter='|', low_memory=False)
        self.slownet = pickle.load(open('../../res/slownet_extended.graph', 'rb'))

    def link_entities(self):
        match_counter = dict()
        csv_file = open('../../res/dsb_slownet_links.csv', 'w')
        fieldnames = ['dsb_sense_id', 'slownet_synset_id']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter='|')
        writer.writeheader()
        for synset_id in self.slownet.nodes:
            # Iterate over synsets in SloWnet
            slo_literals = self.slownet.nodes[synset_id]['slo_literals']
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

                    if (len(matching_synonyms) > 0):
                        row = {'dsb_sense_id': candidate['sense_id'], 'slownet_synset_id': synset_id}
                        writer.writerow(row)
        
        csv_file.close()
        print(match_counter)


def main():
    t1 = time.time()
    linker = Linker()
    linker.link_entities()
    t2 = time.time() - t1
    print('TOTAL TIME ELAPSED: ' + str(t2))

if __name__ == "__main__":
    main()