from typing import *
from concurrent.futures import ProcessPoolExecutor, Future
from collections import defaultdict
import networkx as nx
import numpy as np
from utils import *
from pymongo import MongoClient
from flask import Flask, jsonify, url_for, redirect


app = Flask(__name__, static_folder='static', static_url_path='/')
client = MongoClient('localhost', 27017)
db = client['diva-proj']
pool = ProcessPoolExecutor()
graph_frames: List[Future] = []


def format_for_g6(g: nx.Graph):
    nodes = [{'id': nid, 'label': nid, 'size': g.nodes[nid]['points']} for nid in g.nodes]
    edges = [{'source': p, 'target': q, 'weight': g.edges[p,q]['weight']} for p,q in g.edges]
    # edges = [{'source': p, 'target': q} | g.edges[p,q] for p,q in g.edges]

    data = {
        'nodes': nodes,
        'edges': edges
    }

    return data


@app.route("/")
def index():
    global pool
    global i
    global jobs
    jobs = []
    i = 0
    pool.shutdown(wait=False, cancel_futures=True)
    pool = ProcessPoolExecutor()
    return redirect(url_for('static', filename='index.html'))


def work(start, end):

    query = {'publication_date': {'$gte': start, '$lte': end}}
    papers = list(db.papers.find(query).sort('publication_date'))
    papers = [p for p in papers if p['cited_by_count'] > 100]
    # ml_concepts = set(c['id'] for c in db.concepts.find() if c['level'] == 1)
    ml_concepts = set(c['id'] for c in db.concepts.find({'level': 2, "ancestors.id": 'https://openalex.org/C119857082'}))

    concept_paper_map = defaultdict(float)
    concept_num_map = defaultdict(int)
    for p in papers:
        total_score = sum(float(c['score']) for c in p['concepts'])
        for c in p['concepts']:
            if c['id'] in ml_concepts:
                if float(c['score']) > 0.3:
                    concept_paper_map[(c['id'], c['display_name'])] += float(c['score']) / total_score
                    concept_num_map[(c['id'], c['display_name'])] += 1

    g = nx.Graph()
    g.add_nodes_from([name for _, name in concept_paper_map.keys()])
    for k,v in concept_paper_map.items():
        _, name = k
        g.nodes[name]['points'] = v / concept_num_map[k]


    edges = []
    for p in papers:
        concepts = (c for c in p['concepts'] if c['id'] in ml_concepts)
        # concepts = (c for c in concepts if float(c['score']) > 0.4)
        concepts = (c['display_name'] for c in concepts)
        edges.extend(list(itertools.combinations(concepts, 2)))

    edges = [sorted(e) for e in edges]
    edges = [(e[0], e[1]) for e in edges]
    counter = Counter(edges)
    edges = [(p, q, {'weight': w}) for (p,q), w in counter.items()]
    g.add_edges_from(edges)

    g = normalize_node_attributes(g, 'points')
    g = normalize_edge_attribute(g, 'weight')

    print(np.mean([g.nodes[n]['points'] for n in g.nodes]))
    print(np.std([g.nodes[n]['points'] for n in g.nodes]))
    print('====')
    
    g.remove_edges_from([(p,q) for p,q in g.edges if g.edges[p,q]['weight'] == 0])
    g.remove_nodes_from([n for n in g.nodes if g.nodes[n]['points'] < 0.1])
    g.remove_nodes_from([n for n in g.nodes if g.degree[n] == 0])

    g = normalize_node_attributes(g, 'points')
    g = normalize_edge_attribute(g, 'weight')

    data = format_for_g6(g)
    return data



i = 0
@app.route("/data/<int:frame_number>")
def get_data(frame_number):
    i = frame_number
    
    year_windows = list(iterate_windows_over_range(2005, 2020))
    print(i)

    if i == 0:
        # This is the first iteration. Start all jobs parallely
        for start, end in year_windows:
            future = pool.submit(work, start, end)
            graph_frames.append(future)


    data = graph_frames[i].result()

    # start, end = year_windows[i]
    # data = work(start, end)
    # payload = {'frame': i, 'data': data}
    print(year_windows[i])
    # i = (i + 1) % len(year_windows)
    return jsonify(data)


if __name__ == '__main__':
    app.run(debug=True)
