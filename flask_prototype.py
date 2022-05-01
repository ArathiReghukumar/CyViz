# from pymongo import MongoClient
# import networkx as nx
# import itertools
# from typing import *

# from utils import *

# from flask import Flask, url_for, jsonify

# app = Flask(__name__, static_folder='static', static_url_path='/')
# graph_snapshots: List[nx.Digraph] = []




# @app.route("/")
# def index():
#     return url_for('static', filename='index.html')

# @app.route("/data")
# def get_data():
#     g = graph_snapshots[0]
#     g.number_of_nodes(), g.number_of_edges()
#     nodes = [{'id': nid, 'label': nid} for nid in g.nodes]
#     edges = [{'source': p, 'target': q} for p,q in g.edges]

#     data = {
#         'nodes': nodes,
#         'edges': edges
#     }

#     return jsonify(data)
    

# if __name__ == '__main__':
    
#     client = MongoClient('localhost', 27017)
#     db = client['diva-proj']
#     papers = db.papers
#     windows = iterate_windows_over_range(2020, 2021)
#     windows = list(windows)

#     # graph_snapshots = []

#     for start, end in tqdm(windows):
#         res = get_papers_in_window(papers, start, end)
#         res = [
#             (p['wid'], [ref.split('/')[-1] for ref in p['referenced_works']])
#             for p in res
#         ]
#         res = filter(lambda x: len(x[1]) > 0, res)
#         res = (zip(itertools.repeat(p), q) for p,q in res)
#         res = itertools.chain.from_iterable(res)
#         res = list(res)
#         G = nx.DiGraph()
#         G.add_edges_from(res)

#         pagerank_scores = nx.pagerank(G)
#         pagerank_scores = normalize_pagerank_scores(pagerank_scores)

#         min_pagerank_threshold = 0.01
#         to_remove_nodes = [k for k,v in pagerank_scores.items() if v < min_pagerank_threshold]
#         G.remove_nodes_from(to_remove_nodes)
#         to_remove = [k for k,v in G.in_degree if v == 0]
#         G.remove_nodes_from(to_remove)

#         graph_snapshots.append(G)


#     app.run()


