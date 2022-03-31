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


page = Blueprint('view2', __name__)
client = MongoClient('localhost', 27017)
db = client['diva-proj']
mycol=db['authors']
# pool = ProcessPoolExecutor()
# graph_frames: List[Future] = []


def format_for_g6(g: nx.Graph):
    nodes = [{'id': nid, 'label': g.nodes[nid]['label']} for nid in g.nodes] 
    edges = [{'source': p, 'target': q} for p,q in g.edges]
    #edges = [{'source': p, 'target': q} | g.edges[p,q] for p,q in g.edges]
    data = {
        'nodes': nodes,
        'edges': edges
    }
    return data



def author():
    author_works = list(mycol.find({'Jason Priem': {'$exists': True}}))[0]
    author_works = author_works['Jason Priem']
    
    g2=nx.Graph()
    author_name='Jason Priem'

    all_referenced = dict()
    for auth_paper, references in author_works.items():
        for r in references:
            all_referenced[r['id']] = r
    
    all_referenced = list(all_referenced.values())
    all_referenced = [p for p in all_referenced if p['cited_by_count']>3]

    

    g2.add_node(author_name)
    g2.nodes[author_name]['label'] = author_name
    for paper in all_referenced:
        paper_id = paper['id']
        g2.add_node(paper_id)    
        g2.nodes[paper_id]['label'] = paper['display_name']


    for paper in all_referenced:
        g2.add_edge(author_name, paper['id'])

    
    for paper in all_referenced:
        for citation in paper['referenced_works']:
            if citation in g2.nodes:
                g2.add_edge(paper['id'], citation)

    

    author_data = format_for_g6(g2)
    return author_data



@page.route("/view2")
def view2_index():
    return redirect(url_for('static', filename='view2/index.html'))


@page.route("/authors")
def get_author_data():
    data = author()
    return jsonify(data)


