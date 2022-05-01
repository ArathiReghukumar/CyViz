from typing import *
from concurrent.futures import ProcessPoolExecutor, Future
from collections import defaultdict
import networkx as nx
import numpy as np
from utils import *
from pymongo import MongoClient
from flask import Blueprint, jsonify, url_for, redirect
import itertools
from pprint import pprint

from colorhash import ColorHash

page = Blueprint('view5', __name__)
client = MongoClient('localhost', 27017)
db = client['diva-proj']
mycol2=db['authors_ss']
# pool = ProcessPoolExecutor()
# graph_frames: List[Future] = []


def format_for_g6(g: nx.Graph):
    nodes = [{
        'id': nid, 
        'label': g.nodes[nid]['label'],
        'concept': g.nodes[nid]['concept'],
        'style': {'fill': ColorHash(g.nodes[nid]['concept']).hex}
        } for nid in g.nodes] 
    edges = [{'source': p, 'target': q} for p,q in g.edges]
    #edges = [{'source': p, 'target': q} | g.edges[p,q] for p,q in g.edges]
    data = {
        'nodes': nodes,
        'edges': edges
    }
    return data



def author_ss():
    author_works = list(mycol2.find({'Saed Sayad': {'$exists': True}}))[0]
    author_works = author_works['Saed Sayad']
    g2=nx.Graph()
    author_name='Saed Sayad'

    all_referenced = dict()
    for auth_paper, references in author_works.items():
        for r in references:
            all_referenced[r['id']] = r
    
    all_referenced = list(all_referenced.values())
    all_referenced = [p for p in all_referenced]

    

    filtered = []
    for p in all_referenced:
        if p['cited_by_count'] is not None: 
            if p['cited_by_count'] > 0:
                filtered.append(p)

    # print(filtered)
    

    g2.add_node(author_name)
    g2.nodes[author_name]['label'] = author_name
    g2.nodes[author_name]['concept'] = author_name
    for paper in filtered:
        paper_id = paper['id']
        g2.add_node(paper_id)    
        g2.nodes[paper_id]['label'] = paper['display_name']
        g2.nodes[paper_id]['concept'] = [c['display_name'] for c in paper['concepts'] if c['level'] == 0][0]
        # print(g2.nodes[paper_id]['concept'])


    for paper in filtered:
        g2.add_edge(author_name, paper['id'])

    
    for paper in filtered:
        for citation in paper['referenced_works']:
            if citation in g2.nodes:
                g2.add_edge(paper['id'], citation)




    author_data = format_for_g6(g2)
    return author_data

@page.route("/view5")
def view5_index():
    return redirect(url_for('static', filename='view5/index.html'))


@page.route("/view5/authorsss")
def get_author_data2():
    data = author_ss()
    #print(data)
    return jsonify(data)