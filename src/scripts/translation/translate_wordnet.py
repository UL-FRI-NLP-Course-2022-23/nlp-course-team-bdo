import pickle as pkl
import networkx as nx
from lxml import etree

import re
import json
import requests

slownet_graph_output_filepath = "../../../res/wordnet_slownet.graph"

class Translator:

    def __init__(self):

        self.translator_setup()

    def translator_setup(self):

        with open(slownet_graph_output_filepath, 'rb') as slownet_file:

            # setup wordnet graph
            self.slownet = pkl.load(slownet_file)
        
        # URL for running docker API
        self.nemo_url = 'http://localhost:4001/api/translate'

        # regex to keep only spaces and alphabet chars
        self.alpha_filter = re.compile('[^a-zA-Z\s]')

    def translate_wordnet(self, only_new = True):
        """Translate entire wordnet

        Args:
            only_new (bool, optional): translate only synsets with no words. Defaults to True.
        """

        # list of all synsets ids
        synsets = list(trans.slownet.nodes)
        num_synsets = len(synsets)

        for ind, synset_id in zip(range(num_synsets), synsets):

            # specific synset
            node = trans.slownet.nodes[synset_id]

            if not only_new or len(node['slo_literals']) == 0:
                
                self.translate_synset(node)

            if ind % 10 == 0:

                print(f'Translated {ind}/{num_synsets} synsets.', end = '\r')

    def transation_request(self, text):
        """Send a translation request to NeMo API.

        Args:
            text (str): string to translate

        Returns:
            str: translated string
        """

        fields = {
                        "src_language": "en",
                        "tgt_language": "sl",
                        "text": text
                    }
        
        # send request
        json_data = json.dumps(fields).encode('utf8')

        res = requests.post(url=self.nemo_url, data=json_data)

        res_data = res.json()

        # extract translation
        translation = res_data['result']

        return translation

    def translate_word(self, word):
        """Translate a single word into slovenian.

        Args:
            word (str): english word

        Returns:
            (str, float): slovenian word, probability
        """

        translation = self.transation_request(word)

        translation = self.alpha_filter.sub('', translation)

        translations = [(translation, 1.00)]

        return translations
    
    def translate_list(self, wordlist):
        """Translate array of words into array of slovenian word

        Args:
            wordlist (list[str]): english synonims

        Returns:
            list[(str, float)]: array of (slovenian word, probability)
        """

        translation = self.transation_request(wordlist)

        translations =[]

        # split into multiple synonyms
        for t in translation.split(', '):

            ts = self.alpha_filter.sub('', t)
            
            translations.append((ts, 1.00))

        return translations

    def translate_corpora():

        pass

    def translate_synset(self, node, mode = 'list'):
        """Translate entire synset (in-place).

        Args:
            node (dict): networkx node attributes
            mode (str, optional): translate word individually or concat everything together.  Defaults to 'list'.

        Returns:
            dict: same node but with filled in dict
        """

        slo_literals = set(node['slo_literals'])

        if mode == 'single' or len(node['eng_literals']) == 1:

            for eng_literal in node['eng_literals']:

                translations = self.translate_word(eng_literal)

                for translation in translations:

                    slo_literals.add(translation[0])

        elif mode == 'list':
            
            # combine all synonyms into one sentence
            eng_list = ', '.join(node['eng_literals'])

            translations = self.translate_list(eng_list)

            for translation in translations:

                slo_literals.add(translation[0])

        slo_literals = list(slo_literals)

        node['slo_literals'] = slo_literals

        return node


if __name__ == '__main__':

    trans = Translator()

    from random import choice

    # randomly translate a synset
    rnd_node = choice(list(trans.slownet.nodes))
    rnd_node_dict = trans.slownet.nodes[rnd_node]
    
    trans.translate_synset(rnd_node_dict)
    print(rnd_node_dict)

    # print(trans.translate_wordnet())