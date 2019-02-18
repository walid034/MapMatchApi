from flask import Flask, request, jsonify
import math
from leuvenmapmatching.matcher.distance import DistanceMatcher
from leuvenmapmatching.map.inmem import InMemMap
from leuvenmapmatching import visualization as mmviz
import osmread
from osmread import parse_file, Way
import numpy as np
from geopy.distance import geodesic
import ast

nodeinfo = []
mapgraph = InMemMap("myosm", use_latlon=True, use_rtree=True, index_edges=True)
for entity in osmread.parse_file('map.osm'):
    if isinstance(entity, osmread.Way) and 'highway' in entity.tags:
        for node_a, node_b in zip(entity.nodes, entity.nodes[1:]):
            mapgraph.add_edge(node_a, node_b)
            mapgraph.add_edge(node_b, node_a)
    if isinstance(entity, osmread.Node):
        mapgraph.add_node(entity.id, (entity.lat, entity.lon))
        nodeinfo.append([entity.id, entity.lat, entity.lon])
mapgraph.purge()
nodeinfo = np.array(nodeinfo)

def getdistance(nodeslist):
    i=0
    totaldist = 0
    while(i+1<len(nodeslist)):
        r1 = np.where(nodeinfo[:,0]==nodeslist[i])
        r2 = np.where(nodeinfo[:,0]==nodeslist[i+1])

        coords_1 = (nodeinfo[r1, 1:3][0][0][0], nodeinfo[r1, 1:3][0][0][1])
        coords_2 = (nodeinfo[r2, 1:3][0][0][0], nodeinfo[r2, 1:3][0][0][1])
        
        totaldist = totaldist+geodesic(coords_1, coords_2).km
        i+=1
    return (totaldist)

app = Flask(__name__)

@app.route('/', methods=['POST'])

def getcoord():
    coordinates = request.json["coordinates"]
    matcher = DistanceMatcher(mapgraph, max_dist=80, obs_noise_ne=math.inf, non_emitting_states=True)
    states = matcher.match(coordinates, unique = True)
    nodes = matcher.path_pred_onlynodes

    nodelist = []
    coordlist = []
    for m in matcher.lattice_best:
        nodelist.append(m.edge_m.l1)
        coordlist.append(m.edge_m.p1)

    return jsonify(
        {'MatchedCoordinates': coordlist, 'MatchedDistance': getdistance(nodelist)}
        )

app.run(debug = True, port = 8080)
    