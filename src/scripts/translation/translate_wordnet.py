import pickle as pkl
import networkx as nx
from lxml import etree

import os

import re
import json
import requests
import classla

import signal

slownet_graph_output_filepath = "../../../res/wordnet_slownet.graph"
slownet_extended_filepath = "../../../res/slownet_extended.graph"

class timeout:
    def __init__(self, seconds=1, error_message='Timeout'):
        self.seconds = seconds
        self.error_message = error_message
    def handle_timeout(self, signum, frame):
        raise TimeoutError(self.error_message)
    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)
    def __exit__(self, type, value, traceback):
        signal.alarm(0)

class Translator:

    def __init__(self):

        self.translator_setup()

    def translator_setup(self):

        if os.path.exists(slownet_extended_filepath):

            with open(slownet_extended_filepath, 'rb') as slownet_file:

                # setup wordnet graph
                self.slownet = pkl.load(slownet_file)

        else:

            with open(slownet_graph_output_filepath, 'rb') as slownet_file:

                # setup wordnet graph
                self.slownet = pkl.load(slownet_file)
        
        # URL for running docker API
        self.translate_api_url = 'http://localhost:4001/api/translate'
        self.reverse_translate_api_url = 'http://localhost:4000/api/translate'

        # regex to keep only spaces and alphabet chars
        self.alpha_filter = re.compile('[^\w^\s]+')

        self.nlp = classla.Pipeline(lang = 'sl', processors = 'tokenize,pos,lemma')

    def lemmatize(self, word):

        doc = self.nlp(word)

        return doc.sentences[0].words[0].lemma

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

        # cleaning of translations
        old_ts = translation

        with timeout(seconds=5):
                
            try:

                translation = self.lemmatize(translation)

            except TimeoutError:

                translation = old_ts

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

            ts = ts.replace('angleščina', '')
            ts = ts.replace('angleško', '')
            ts = ts.replace('(angleško)', '')
            ts = ts.replace('(angleščina)', '')

            old_ts = ts
            
            with timeout(seconds=5):
                
                try:

                    ts = self.lemmatize(ts)

                except TimeoutError:

                    ts = old_ts
            
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

        synset_type = node['synset_id'][-1]

        node['confidences'] = {}

        slo_literals = set(node['slo_literals'])

        eng_literals = [eng_literal for eng_literal in node['eng_literals']]

        for slo_literal in slo_literals:
            
            # we assume with high degree of certainty that previous translations are correct
            node['confidences'][slo_literal] = 0.81

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

        # set confidences for each translation
        for slo_literal in slo_literals:

            if slo_literal not in node['confidences'].keys():

                node['confidences'][slo_literal] = 0.38
        
        # reverse translate to check if bijection
        if cautious:

            verified_literals = []

            eng_literals = set(eng_literals)

            if mode == 'single' or len(slo_literals) == 1:

                for slo_literal in slo_literals:

                    translations = self.translate_word(slo_literal, reverse = True)

                    is_bijection = False

                    for translation in translations:

                        raw_translation = translation[0]

                        cleaned_translation = raw_translation.lower()
                        cleaned_translation = cleaned_translation.replace('the', '')
                        cleaned_translation = cleaned_translation.replace('\'', '')

                        if cleaned_translation in eng_literals:

                            is_bijection = True

                    verified_literals.append(slo_literal)

                    if is_bijection:

                        node['confidences'][slo_literal] += 0.1

            elif mode == 'list':

                translations = self.translate_list(slo_literals, reverse = True)

                for i in range(len(translations)):

                    raw_translation = translations[i][0]

                    cleaned_translation = raw_translation.lower()
                    cleaned_translation = cleaned_translation.replace('the', '')
                    cleaned_translation = cleaned_translation.replace('\'', '')

                    verified_literals.append(slo_literals[i])
                    
                    if cleaned_translation in eng_literals:

                        node['confidences'][slo_literals[i]] += 0.1

            slo_literals = verified_literals

        # add translated slovenian literals
        node['slo_literals'].extend(slo_literals)
        node['slo_literals'] = list(set(node['slo_literals']))

        return node


if __name__ == '__main__':

    trans = Translator()

    from random import choice

    # randomly translate a synset
    rnd_node = choice(list(trans.slownet.nodes))
    rnd_node_dict = trans.slownet.nodes[rnd_node]
    
    trans.translate_synset(rnd_node_dict)
    print(rnd_node_dict)

    # translate entirety of wordnet
    trans.translate_wordnet(only_new = True)