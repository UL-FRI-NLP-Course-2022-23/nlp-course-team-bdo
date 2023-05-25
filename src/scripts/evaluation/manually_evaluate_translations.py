import datetime
import pickle

import numpy as np
from networkx import Graph

sample_nodes_file = open('../../../res/evaluation/sample_nodes_ids.txt', 'r').read().split('#')[1:]
nemo_nodes = sample_nodes_file[0].split('\n')[1:]
all_nodes = sample_nodes_file[1].split('\n')[1:]
original_nodes = sample_nodes_file[2].split('\n')[1:]

slownet_extended_graph_filepath = '../../../res/slownet_extended.graph'
wordnet_slownet_graph_filepath = '../../../res/wordnet_slownet.graph'

slowenet_extended: Graph = pickle.load(open(slownet_extended_graph_filepath, 'rb'))
wordnet_graph: Graph = pickle.load(open(slownet_extended_graph_filepath, 'rb'))
slownet_graph: Graph = wordnet_graph.subgraph(
    [node for node in wordnet_graph.nodes if len(wordnet_graph.nodes[node]["slo_literals"]) > 0])

nemo_nodes = [slowenet_extended.nodes[node_id] for node_id in nemo_nodes if len(node_id) > 0]
all_nodes = [slowenet_extended.nodes[node_id] for node_id in all_nodes if len(node_id) > 0]
extended_nodes = [slownet_graph.nodes[node_id] for node_id in original_nodes if len(node_id) > 0]
nodes_to_evaluate = input("Which nodes to evaluate (nemo/all/original): ")

if nodes_to_evaluate == 'nemo':
    nodes_to_evaluate = nemo_nodes
elif nodes_to_evaluate == 'all':
    nodes_to_evaluate = all_nodes
else:
    nodes_to_evaluate = original_nodes

scores = []
with open('../../../res/evaluation/all_nodes_score.txt', 'a') as f:
    current_time = datetime.datetime.now()
    f.write("\nTime: " + str(current_time) + "\n")
    correct_num = 0
    for node in nodes_to_evaluate:
        print("slo literals: ", node['slo_literals'])
        print("eng literals: ", node['eng_literals'])
        score = float(input("Correct number of literals for " + node['synset_id'] + ": ")) / len(node['slo_literals'])
        scores.append(score)
        f.write(node["synset_id"] + " - " + str(score) + "\n")
        print("---")

    print("Average: ", np.average(scores))
    print("Standard deviation: ", np.std(scores))

