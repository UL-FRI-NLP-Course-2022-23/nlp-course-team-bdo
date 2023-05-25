import pickle
import time
from networkx import Graph
from random import sample
from lxml import etree


def sample_nodes(nodes, sample_size):
    noun_nodes = []
    adj_nodes = []
    verb_nodes = []
    b_nodes = []

    for node_id in nodes:
        word_type = node_id[-1]
        if len(slowenet_extended.nodes[node_id]['slo_literals']) > 0:
            if word_type == 'n':
                noun_nodes.append(node_id)
            elif word_type == 'a':
                adj_nodes.append(node_id)
            elif word_type == 'v':
                verb_nodes.append(node_id)
            elif word_type == 'b':
                b_nodes.append(node_id)

    noun_nodes = sample(noun_nodes, int(sample_size / 4))
    adj_nodes = sample(adj_nodes, int(sample_size / 4))
    verb_nodes = sample(verb_nodes, int(sample_size / 4))
    b_nodes = sample(b_nodes, int(sample_size / 4))

    return noun_nodes + adj_nodes + verb_nodes + b_nodes


slownet_extended_graph_filepath = '../../../res/slownet_extended.graph'
wordnet_slownet_graph_filepath = '../../../res/wordnet_slownet.graph'
slownet_xml_filepath = "../../../res/slownet-2015-05-07.xml"

sample_size = 10

start = time.time()
print("Loading graph...")
slowenet_extended: Graph = pickle.load(open(slownet_extended_graph_filepath, 'rb'))
wordnet_graph: Graph = pickle.load(open(wordnet_slownet_graph_filepath, 'rb'))
slownet_graph: Graph = wordnet_graph.subgraph(
    [node for node in wordnet_graph.nodes if len(wordnet_graph.nodes[node]["slo_literals"]) > 0])

print("Sampling nodes...")
root_slownet = etree.parse(slownet_xml_filepath)
synsets = root_slownet.xpath("//SYNSET")

auto_synset_ids = []
manual_synset_ids = []
other_synset_ids = []
for synset in synsets:
    slo_literals_type = synset.xpath("SYNONYM[@xml:lang='sl']/LITERAL/@lnote")
    if len(slo_literals_type) > 0:
        is_auto = slo_literals_type[0] == 'auto'
        if is_auto:
            auto_synset_ids.append(synset.xpath("ID/text()")[0])
        else:
            manual_synset_ids.append(synset.xpath("ID/text()")[0])
    else:
        other_synset_ids.append(synset.xpath("ID/text()")[0])

with open('../../../res/evaluation/sample_nodes_ids.txt', 'w') as f:
    f.write("# nemo_automatic\n")
    for node in sample_nodes(other_synset_ids, sample_size):
        f.write(node + '\n')
    f.write('\n')

    f.write("# all_together\n")
    for node in sample_nodes(auto_synset_ids + manual_synset_ids + other_synset_ids, sample_size):
        f.write(node + '\n')
    f.write('\n')

    f.write("# original_slownet\n")
    for node in sample_nodes(slownet_graph.nodes, sample_size):
        f.write(node + '\n')
