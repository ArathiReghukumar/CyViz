from typing import *
from concurrent.futures import ProcessPoolExecutor, Future

from collections import defaultdict
from flask import Blueprint, jsonify, url_for, redirect, request
import networkx as nx
from pymongo import MongoClient
from utils import *

client = MongoClient('localhost', 27017)
db = client['diva-proj']


page = Blueprint('view1', __name__)
pool = ProcessPoolExecutor()
graph_frames: List[Future] = []


def format_for_g6(g: nx.Graph):
    nodes = [{
        'id': nid, 
        'label': '\n'.join(nid.split(' ')), 
        'size': g.nodes[nid]['points'],
        'cid': g.nodes[nid]['cid']
    } for nid in g.nodes]
    edges = [{'source': p, 'target': q, 'weight': g.edges[p,q]['weight']} for p,q in g.edges]

    data = {
        'nodes': nodes,
        'edges': edges
    }

    return data


def level1(start, end):
    query = {'publication_date': {'$gte': start, '$lte': end}}
    papers = list(db.papers.find(query).sort('publication_date'))
    papers = [p for p in papers if p['cited_by_count'] > 150]
    # ml_concepts = set(c['id'] for c in db.concepts.find() if c['level'] == 1)
    # ml_concepts = set(c['id'] for c in db.concepts.find({'level': 1, "ancestors.id": 'https://openalex.org/C41008148'}))
    ml_concepts = set(c['id'] for c in db.concepts.find({'level': 1}))

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
        idx, name = k
        g.nodes[name]['points'] = v / concept_num_map[k]
        g.nodes[name]['cid'] = idx


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

    # g = normalize_node_attributes(g, 'points')
    # g = normalize_edge_attribute(g, 'weight')
    
    # g.remove_edges_from([(p,q) for p,q in g.edges if g.edges[p,q]['weight'] == 0])
    # g.remove_nodes_from([n for n in g.nodes if g.nodes[n]['points'] < 0.1])
    # g.remove_nodes_from([n for n in g.nodes if g.degree[n] == 0])

    g = normalize_node_attributes(g, 'points')
    g = normalize_edge_attribute(g, 'weight')

    data = format_for_g6(g)
    return data

def level2(start, end):
    query = {'publication_date': {'$gte': start, '$lte': end}}
    papers = list(db.papers.find(query).sort('publication_date'))
    papers = [p for p in papers if p['cited_by_count'] > 150]
    # ml_concepts = set(c['id'] for c in db.concepts.find({'level': 2, "ancestors.id": 'https://openalex.org/C41008148'}))
    ml_concepts = set(c['id'] for c in db.concepts.find({'level': 2}))

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
        idx, name = k
        g.nodes[name]['points'] = v / concept_num_map[k]
        g.nodes[name]['cid'] = idx


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
    
    g.remove_edges_from([(p,q) for p,q in g.edges if g.edges[p,q]['weight'] == 0])
    # g.remove_nodes_from([n for n in g.nodes if g.nodes[n]['points'] < 0.1])
    # g.remove_nodes_from([n for n in g.nodes if g.degree[n] == 0])

    g = nx.k_core(g, k=2)

    g = normalize_node_attributes(g, 'points')
    g = normalize_edge_attribute(g, 'weight')

    data = format_for_g6(g)
    return data


def work(start, end):
    level1_data = level1(start, end)
    level2_data = level2(start, end)
    return {'level1': level1_data, 'level2': level2_data}



@page.route("/view1")
def index():
    global pool
    global i
    i = 0
    pool.shutdown(wait=False, cancel_futures=True)
    pool = ProcessPoolExecutor()
    return redirect(url_for('static', filename='view1/index.html'))


@page.route('/view1/papers')
def get_papers():
    cid1 = request.args.get('cid1')
    cid2 = request.args.get('cid2')
    frame_number = int(request.args.get('frame_number'))
    print(cid1, cid2, frame_number)

    year_windows = list(iterate_windows_over_range(2015, 2021))
    start, end = year_windows[frame_number]


    query = {
        '$and': [
            {"concepts.id": cid1}, {"concepts.id": cid2},
            {'publication_date': {'$gte': start, '$lte': end}}
        ]
    }

    # print(query)
    res = []
    for p in db.papers.find(query).limit(20).sort('cited_by_count', -1):
        res.append({
            'name': p['display_name'],
            'link': p['id']
        })

    print(res)

    return jsonify({'papers': res})



i = 0
@page.route("/view1/data/<int:frame_number>")
def get_data(frame_number):
    i = frame_number
    
    year_windows = list(iterate_windows_over_range(2012, 2021))
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