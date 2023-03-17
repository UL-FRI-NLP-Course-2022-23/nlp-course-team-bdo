import pickle
import time
import networkx as nx
from lxml import etree

slownet_filepath = "../../res/slownet-2015-05-07.xml"
slownet_graph_output_filepath = "../../res/wordnet_slownet.graph"

# parsing slownet xml
root_slownet = etree.parse(slownet_filepath)
synsets = root_slownet.xpath("//SYNSET")

start = time.time()
print("Constructing nodes... (may take from 10 - 15 seconds)")

wordnet_graph = nx.Graph()
synset_nodes = {}
for synset in synsets:
    synset_id = synset.xpath("ID/text()")[0]
    eng_literals = synset.xpath("SYNONYM[@xml:lang='en']/LITERAL/text()")
    slo_literals = synset.xpath("SYNONYM[@xml:lang='sl']/LITERAL/text()")
    connections = synset.xpath("ILR")
    wordnet_snyset_node = {
        "synset_id": synset_id,
        "eng_literals": eng_literals,
        "slo_literals": slo_literals,
        "connections": [{"type": connection.xpath("@type")[0], "synset_id": connection.xpath("text()")[0]} for connection in connections],
    }

    synset_nodes[synset_id] = wordnet_snyset_node
    wordnet_graph.add_node(synset_id, **wordnet_snyset_node)

print("Time taken to construct nodes:", time.time() - start)
start = time.time()
print("Constructing edges...")

for synset_id, synset_data in synset_nodes.items():
    for connection in synset_data["connections"]:
        end_node_synset_id = connection["synset_id"]
        connection_type = connection["type"]
        wordnet_graph.add_edge(synset_id, end_node_synset_id, type=connection_type)

print("Time taken to construct edges:", time.time() - start)

# serialize wordnet graph for faster access
pickle.dump(wordnet_graph, open(slownet_graph_output_filepath, 'wb'))

print("\nSerialized graph to file:", slownet_graph_output_filepath)
