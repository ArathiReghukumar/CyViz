# from crypt import methods
from typing import *
import numpy as np
from concurrent.futures import ProcessPoolExecutor, Future

from collections import defaultdict
from flask import Blueprint, jsonify, url_for, redirect, request
import networkx as nx
from pymongo import MongoClient
from utils import *
from pprint import pprint
from colorhash import ColorHash

client = MongoClient('localhost', 27017)
db = client['diva-proj']


page = Blueprint('view1', __name__)
pool = ProcessPoolExecutor(max_workers=8)
graph_frames = defaultdict(list)

def color_variant(hex_color, brightness_offset=1):
    """ takes a color like #87c95f and produces a lighter or darker variant """
    if len(hex_color) != 7:
        raise Exception("Passed %s into color_variant(), needs to be in #87c95f format." % hex_color)
    rgb_hex = [hex_color[x:x+2] for x in [1, 3, 5]]
    new_rgb_int = [int(hex_value, 16) + brightness_offset for hex_value in rgb_hex]
    new_rgb_int = [min([255, max([0, i])]) for i in new_rgb_int] # make sure new values are between 0 and 255
    # hex() produces "0x88", we want just "88"
    return "#" + "".join([hex(i)[2:] for i in new_rgb_int])

def format_for_g6(g: nx.Graph):

    def get_color(node):
        if 'ancestor' in node:
            base =  ColorHash(node['ancestor']).hex
        else:
            base =  ColorHash(node['cid']).hex

        
        return {
            'fill': base,
            'shadowColor': '#424887',
            'stroke': '#424887'
        }

    
    nodes = [{
        'id': g.nodes[nid]['cid'], 
        'label': '\n'.join(nid.split(' ')), 
        'size': g.nodes[nid]['points'],
        'cid': g.nodes[nid]['cid'],
        'style': {
            'fill': get_color(g.nodes[nid])['fill'],
            'stroke': get_color(g.nodes[nid])['fill']
        },
        'stateStyles': {
            'selected': {
                'fill': get_color(g.nodes[nid])['fill'],
                'shadowColor': get_color(g.nodes[nid])['shadowColor'],
                'stroke': get_color(g.nodes[nid])['stroke'],
                'shadowBlur': 10,
                'lineWidth': 5,
            },
            'active': {
                'fill': color_variant(get_color(g.nodes[nid])['fill'], -10),
                'shadowColor': get_color(g.nodes[nid])['shadowColor'],
                'stroke': get_color(g.nodes[nid])['stroke'],
                'shadowBlur': 10,
                'lineWidth': 3,
            },
            'inactive': {
                'fill': color_variant(get_color(g.nodes[nid])['fill'], 110),
            }
        }
    } for nid in g.nodes]


    edges = [{
        'source': g.nodes[p]['cid'], 
        'target': g.nodes[q]['cid'], 
        'weight': g.edges[p,q]['weight'],
        'style': {'opacity': g.edges[p,q]['weight'], 'lineWidth': 3}
    } for p,q in g.edges]

    data = {
        'nodes': nodes,
        'edges': edges
    }

    return data



def level1(start, end):
    query = {
        'publication_date': {'$gte': start, '$lte': end},
        'cited_by_count': {'$gte': 100}
    }
    papers = list(db.papers.find(query))
    # papers = list(db.papers.find(query).sort('publication_date'))
    # papers = [p for p in papers if p['cited_by_count'] > 150]
    # ml_concepts = set(c['id'] for c in db.concepts.find() if c['level'] == 1)
    # ml_concepts = set(c['id'] for c in db.concepts.find({'level': 1, "ancestors.id": 'https://openalex.org/C41008148'}))
    ml_concepts = set(c['id'] for c in db.concepts.find({'level': 1}))

    concept_paper_map = defaultdict(float)
    concept_num_map = defaultdict(int)
    for p in papers:
        total_score = sum(float(c['score']) for c in p['concepts'])
        for c in p['concepts']:
            if c['id'] in ml_concepts:
                if float(c['score']) > 0.2:
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

def level2(start, end, lvl1_concepts_filter):

    query = {
        'publication_date': {'$gte': start, '$lte': end},
        'cited_by_count': {'$gte': 100}
    }

    if len(lvl1_concepts_filter) > 0:
        query['concepts.id'] = {'$in': lvl1_concepts_filter}


    # papers = list(db.papers.find(query).sort('publication_date'))
    papers = list(db.papers.find(query))
    # papers = [p for p in papers if p['cited_by_count'] > 150]
     

    query = {'level': 2}
    if len(lvl1_concepts_filter) > 0:
        query['ancestors.id'] = {'$in': lvl1_concepts_filter}
    relevant_concepts = set(c['id'] for c in db.concepts.find(query))

    if len(lvl1_concepts_filter) > 0:
        cid_ancestor_details = {
            c['id']: [ac['id'] for ac in c['ancestors'] if ac['id'] in lvl1_concepts_filter][-1]
            for c in db.concepts.find(query)
        }

    concept_paper_map = defaultdict(float)
    concept_num_map = defaultdict(int)
    for p in papers:
        total_score = sum(float(c['score']) for c in p['concepts'])
        for c in p['concepts']:
            if c['id'] in relevant_concepts:
                if float(c['score']) > 0.2:
                    concept_paper_map[(c['id'], c['display_name'])] += float(c['score']) / total_score
                    concept_num_map[(c['id'], c['display_name'])] += 1

    g = nx.Graph()
    g.add_nodes_from([name for _, name in concept_paper_map.keys()])
    for k,v in concept_paper_map.items():
        idx, name = k
        g.nodes[name]['points'] = v / concept_num_map[k]
        g.nodes[name]['cid'] = idx

    if len(lvl1_concepts_filter) > 0:
        for n in g.nodes:
            g.nodes[n]['ancestor'] = cid_ancestor_details[g.nodes[n]['cid']]


    edges = []
    for p in papers:
        concepts = (c for c in p['concepts'] if c['id'] in relevant_concepts)
        concepts = (c['display_name'] for c in concepts)
        edges.extend(list(itertools.combinations(concepts, 2)))

    edges = [sorted(e) for e in edges]
    edges = [(e[0], e[1]) for e in edges]
    counter = Counter(edges)
    edges = [(p, q, {'weight': w}) for (p,q), w in counter.items()]
    # pprint(edges)
    g.add_edges_from(edges)

    g.remove_edges_from([(p,q) for p,q in g.edges if g.edges[p,q]['weight'] < 1e-5])
    # g.remove_nodes_from([n for n in g.nodes if g.nodes[n]['points'] < 0.1])
    # g.remove_nodes_from([n for n in g.nodes if g.degree[n] == 0])

    g = nx.k_core(g, k=1)

    # print(g.nodes['Utility']['ancestors'])
   

    g = normalize_node_attributes(g, 'points')
    g = normalize_edge_attribute(g, 'weight')
    
    

    data = format_for_g6(g)
    return data


def work(start, end, lvl1_filter):
    level1_data = level1(start, end)
    level2_data = level2(start, end, lvl1_filter)
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
    # print(cid1, cid2, frame_number)

    year_windows = list(iterate_windows_over_range(1994, 2021))
    start, end = year_windows[frame_number]
    # print(start, end)


    query = {
        '$and': [
            {"concepts.id": cid1}, {"concepts.id": cid2},
            {'publication_date': {'$gte': start, '$lte': end}}
        ]
    }

    
    res = []
    for p in db.papers.find(query).limit(20).sort('cited_by_count', -1):
        res.append({
            'name': p['display_name'],
            'link': p['id']
        })

    return jsonify({'papers': res})



i = 0
@page.route("/view1/data/<int:frame_number>", methods=['GET', 'POST'])
def get_data(frame_number):
    i = frame_number

    metadata = request.get_json()
    print(metadata)
    
    if metadata is not None and metadata != {}:
        metadata['level1_filter'] = frozenset(metadata['level1_filter'])
        metadata = tuple(*metadata.items())
    elif metadata == {}:
        metadata = tuple(*{'level1_filter': frozenset([])}.items())


    # print(metadata, '---', metadata[0])
    # print(metadata in graph_frames)

    
    year_windows = list(iterate_windows_over_range(1994, 2021))
    print(i)

    # if i == 0 and metadata is None:
    if metadata not in graph_frames:
        # This is the first iteration. Start all jobs parallely
        for start, end in year_windows:
            future = pool.submit(work, start, end, [c for c in metadata[1]])
            graph_frames[metadata].append(future)

    data = graph_frames[metadata][i].result()

    # start, end = year_windows[i]
    # data = work(start, end, [c for c in metadata[1]])
    data['year'] = year_windows[i][0].year
    print(year_windows[i][0])
    # i = (i + 1) % len(year_windows)
    return jsonify(data)