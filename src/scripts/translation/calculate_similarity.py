import pickle
import sys

from lxml import etree
from gensim.models import KeyedVectors
from networkx import Graph

slownet_extended_graph_filepath = '../../../res/slownet_extended.graph'
slownet_extended: Graph = pickle.load(open(slownet_extended_graph_filepath, 'rb'))
slownet_xml_filepath = "../../../res/slownet-2015-05-07.xml"

model: KeyedVectors = KeyedVectors.load('../evaluation/vectors-clarin-sl-token.ft.sg.kv', mmap='r')

root_slownet = etree.parse(slownet_xml_filepath)
synsets = root_slownet.xpath("//SYNSET")

auto_synset_ids = []
manual_synset_ids = []
other_synset_ids = []
for synset in synsets:
    slo_literals_type = synset.xpath("SYNONYM[@xml:lang='sl']/LITERAL/@lnote")
    if len(slo_literals_type) == 0:
        other_synset_ids.append(synset.xpath("ID/text()")[0])

print("Updating confidences for", len(other_synset_ids), "synsets...")
for other_node in other_synset_ids:
    current_other_node = slownet_extended.nodes[other_node]
    other_literals = current_other_node["slo_literals"]
    if len(other_literals) < 2:
        continue
    avg_sim = 0
    for literal1 in other_literals:
        original_literal1 = literal1
        sum_sim = 0
        misses = 0
        for literal2 in other_literals:
            literal1 = literal1.lower()
            literal2 = literal2.lower()
            try:
                sum_sim += model.similarity(literal1, literal2)
            except KeyError:
                misses += 1
                pass
        if misses + 1 == len(other_literals):
            sum_sim = 0
        else:
            sum_sim /= len(other_literals)
        avg_sim += sum_sim
    avg_sim /= len(other_literals)
    current_other_node["synonyms_confidence"] = avg_sim

print("Updated synset confidences.")

extended_slownet_with_similarities = "../../../res/slownet_extended_with_similarities.graph"
pickle.dump(slownet_extended, open(extended_slownet_with_similarities, 'wb'))

print("\nSerialized graph to file:", extended_slownet_with_similarities)
