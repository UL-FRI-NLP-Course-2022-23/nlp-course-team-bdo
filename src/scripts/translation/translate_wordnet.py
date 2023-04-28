import pickle as pkl
import networkx as nx
from lxml import etree

import re
import json
import requests

slownet_graph_output_filepath = "../../../res/wordnet_slownet.graph"
slownet_extended_filepath = "../../../res/slownet_extended.graph"

class Translator:

    def __init__(self):

        self.translator_setup()

    def translator_setup(self):

        with open(slownet_graph_output_filepath, 'rb') as slownet_file:

            # setup wordnet graph
            self.slownet = pkl.load(slownet_file)
        
        # URL for running docker API
        self.translate_api_url = 'http://localhost:4001/api/translate'
        self.reverse_translate_api_url = 'http://localhost:4000/api/translate'

        # regex to keep only spaces and alphabet chars
        self.alpha_filter = re.compile('[^\w^\s]+')

    def translate_wordnet(self, only_new = True):
        """Translate entire wordnet.

        Args:
            only_new (bool, optional): translate only synsets with no words. Defaults to True.
        """

        # list of all synsets ids
        synsets = list(self.slownet.nodes)
        num_synsets = len(synsets)

        for ind, synset_id in zip(range(num_synsets), synsets):

            # specific synset
            node = self.slownet.nodes[synset_id]

            if not only_new or len(node['slo_literals']) == 0:
                
                self.translate_synset(node)

            if ind % 10 == 0:

                print(f'Translated {ind}/{num_synsets} synsets.', end = '\r')

            if ind % 100 == 0:

                with open(slownet_extended_filepath, 'wb') as slownet_extended_file:
                    
                    pkl.dump(self.slownet, slownet_extended_file)


    def transation_request(self, text, reverse = False):
        """Send a translation request to NeMo API.

        Args:
            text (str): string to translate

        Returns:
            str: translated string
        """

        api_url = self.translate_api_url if not reverse else self.reverse_translate_api_url

        fields = {
                        "src_language": 'en' if not reverse else 'sl',
                        "tgt_language": 'sl' if not reverse else 'en',
                        "text": text
                    }
        
        # send request
        json_data = json.dumps(fields).encode('utf8')

        res = requests.post(url=api_url, data=json_data)

        res_data = res.json()

        # extract translation
        translation = res_data['result']

        return translation

    def translate_word(self, word, reverse = False):
        """Translate a single word into slovenian.

        Args:
            word (str): english word

        Returns:
            (str, float): slovenian word, probability
        """
        word = f"'{word}'"

        if not reverse: 

            translation = self.transation_request(word)

        else:

            translation = self.transation_request(word, reverse = True)

        translation = self.alpha_filter.sub('', translation)

        translation = translation.replace('(angleško)', '')
        translation = translation.replace('(angleščina)', '')

        translations = [(translation, 1.00)]

        return translations
    
    def translate_list(self, wordlist, reverse = False):
        """Translate array of words into array of slovenian word.

        Args:
            wordlist (list[str]): english synonims

        Returns:
            list[(str, float)]: array of (slovenian word, probability)
        """

        # combine all synonyms into one sentence
        wordlist = ', '.join([f"'{word}'" for word in wordlist])

        if not reverse:

            translation = self.transation_request(wordlist)

        else:

            translation = self.transation_request(wordlist, reverse = True)

        translation = translation.replace('\"', '')
        translation = translation.replace("\'", '')

        translations =[]

        # split into multiple synonyms
        for t in translation.split(', '):

            t = t.strip(' ')

            translation_list = t.split(' ')

            for t in translation_list:

                t = self.alpha_filter.sub('', t)

            t = ' '.join(translation_list)

            ts = self.alpha_filter.sub('', t)

            ts = ts.replace('(angleško)', '')
            ts = ts.replace('(angleščina)', '')
            
            translations.append((ts, 1.00))

        return translations

    def translate_corpora():

        pass

    def translate_synset(self, node, mode = 'list', cautious = False):
        """Translate entire synset (in-place).

        Args:
            node (dict): networkx node attributes
            mode (str, optional): translate word individually or concat everything together.  Defaults to 'list'.

        Returns:
            dict: same node but with filled in dict
        """

        slo_literals = set(node['slo_literals'])

        eng_literals = [eng_literal for eng_literal in node['eng_literals']]

        if mode == 'single' or len(eng_literals) == 1:

            for eng_literal in eng_literals:

                translations = self.translate_word(eng_literal)

                for translation in translations:

                    slo_literals.add(translation[0])

        elif mode == 'list':

            translations = self.translate_list(eng_literals)

            for translation in translations:

                slo_literals.add(translation[0])

        slo_literals = list(slo_literals)
        
        # reverse translate to check if bijection
        if cautious:

            verified_literals = []

            eng_literals = set(eng_literals)

            if mode == 'single' or len(slo_literals) == 1:

                for slo_literal in slo_literals:

                    translations = self.translate_word(slo_literal, reverse = True)

                    is_bijection = False

                    for translation in translations:

                        if translation[0] in eng_literals:

                            is_bijection = True

                    if is_bijection:

                        verified_literals.append(translation[0])

            elif mode == 'list':

                translations = self.translate_list(slo_literals, reverse = True)

                for i in range(len(translations)):
                    
                    if translations[i][0] in eng_literals:

                        verified_literals.append(translation[0])

            slo_literals = verified_literals


        # TODO: Don't remove previously added lists

        node['slo_literals'] = slo_literals

        return node


if __name__ == '__main__':

    trans = Translator()

    from random import choice

    # randomly translate a synset
    # rnd_node = choice(list(trans.slownet.nodes))
    # rnd_node_dict = trans.slownet.nodes[rnd_node]
    
    # trans.translate_synset(rnd_node_dict)
    # print(rnd_node_dict)

    # translate entirety of wordnet
    trans.translate_wordnet()