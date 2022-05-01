#from crypt import methods
#from crypt import methods
#from crypt import methods
from typing import *
from cProfile import run
from concurrent.futures import ProcessPoolExecutor, Future

from collections import defaultdict
from flask import Blueprint, jsonify, render_template, url_for, redirect, request
#from matplotlib.font_manager import _Weight
import networkx as nx
from pymongo import MongoClient
from utils import *
from flask import session
from flask import Flask,g

page = Blueprint('view3', __name__)
client = MongoClient('localhost', 27017)
db = client['diva-proj']
mycol=db['institution']
mycol2=db['institution_all']
c1=0.8

@page.route("/get_count/", methods=['POST','GET'])
def get_count():
    global c1
    c1=request.form.get('count')
    print(c1)
    return redirect(url_for('static', filename='view3/map.html'))

def institution():
    institution_list=list(mycol.find())[0].items()
    institution_list = list(institution_list)[1:]
    institute_pair_counts_map = dict()
    institutes=[]
    for e in institution_list:
        p,q = e
        ins1, ins2 = (p.split('__')[0], p.split('__')[-1])
        count = q
        institute_pair_counts_map[(ins1,ins2)] = count
        institutes.append(ins1)
        institutes.append(ins2)

    institutes=set(institutes)   
    g2=nx.Graph()
    g2.add_nodes_from(institutes)
    all_institution=list(mycol2.find())[0]['institution_data']
    all_institution = {
        i['id']: i
        for i in all_institution  if i['id'] in institutes
    }
    # for inst in all_institution:
    for node in g2.nodes: 
        g2.nodes[node]['latitude'] = all_institution[node]['geo']['latitude']
        g2.nodes[node]['longitude']= all_institution[node]['geo']['longitude']
        g2.nodes[node]['title']=all_institution[node]['display_name']   
    
    cf=float(c1)
    print(cf)
    for (id1, id2), count in institute_pair_counts_map.items():
        g2.add_edge(id1,id2,count=count)

    
    g2 = normalize_edge_attribute(g2, 'count')
    max_l=[]
    
    image=[{ 
        'latitudes': g2.nodes[n]['latitude'],
        'longitudes':g2.nodes[n]['longitude'],
        "svgPath": "M3.5,13.277C3.5,6.22,9.22,0.5,16.276,0.5C23.333,0.5,29.053,6.22,29.053,13.277C29.053,14.54,28.867,15.759,28.526,16.914C26.707,24.271,16.219,32.5,16.219,32.5C16.219,32.5,4.37,23.209,3.673,15.542C3.673,15.542,3.704,15.536,3.704,15.536C3.572,14.804,3.5,14.049,3.5,13.277C3.5,13.277,3.5,13.277,3.5,13.277M16.102,16.123C18.989,16.123,21.329,13.782,21.329,10.895C21.329,8.008,18.989,5.668,16.102,5.668C13.216,5.668,10.876,8.008,10.876,10.895C10.876,13.782,13.216,16.123,16.102,16.123C16.102,16.123,16.102,16.123,16.102,16.123",
        "color": "rgba(75,216,181,0.8)",
        "title":g2.nodes[n]['title']
    }
    for n in g2.nodes]

    # print(len(g2.edges))

    lines=[
            [
                {'latitude': g2.nodes[p]['latitude'],'longitude': g2.nodes[p]['longitude']},
                {'latitude': g2.nodes[q]['latitude'],'longitude': g2.nodes[q]['longitude']},
            ]
        for p,q in g2.edges if g2.edges[p,q]['count'] > cf
    ]

    # print(len(lines))

    return {'image': image, 'multiGeoLine': lines}

@page.route("/view3")
def view3_index():
    return redirect(url_for('static', filename='view3/map.html'))


@page.route("/view3/institution")
def get_institute_data():
    data = institution()
    #print(data)
    return jsonify(data)

# institution()