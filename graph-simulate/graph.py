import networkx as nx


def convert_nodes_to_integers(graph):
    mapping = {i: int(i) for i in graph}
    return nx.relabel_nodes(graph, mapping)

