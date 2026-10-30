"""Build the drivable street graph of central Madrid (inside the M-30) for the web demo.

Input: OpenStreetMap roads of Madrid as GeoJSON, e.g. from
https://raw.githubusercontent.com/amoraschi/spain-cities-geojson/master/cities/madrid.geojson
Output: web/madrid.json, a compact graph with one node per intersection.

    python scripts/build_web_graph.py madrid.geojson
"""
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
BBOX = (-3.7395, 40.3850, -3.6560, 40.4790)  # lon_min, lat_min, lon_max, lat_max, roughly the M-30 ring
MAX_SPEEDS = {  # km/h by road type when the way has no maxspeed (same table as callejero.py)
    "living_street": 20, "residential": 30, "primary_link": 40, "unclassified": 40, "secondary_link": 40,
    "trunk_link": 40, "secondary": 50, "tertiary": 50, "primary": 50, "trunk": 50, "tertiary_link": 50,
    "motorway_link": 70, "motorway": 100,
}
DRIVE = set(MAX_SPEEDS)
MAJOR = {"motorway", "trunk", "primary", "secondary", "tertiary"}
Q = 1e5  # coordinates stored as integers in units of 1e-5 degrees (about 1 m)


def inside(lon, lat):
    return BBOX[0] <= lon <= BBOX[2] and BBOX[1] <= lat <= BBOX[3]


def meters(a, b):
    lat = math.radians((a[1] + b[1]) / 2)
    dx = math.radians(b[0] - a[0]) * math.cos(lat) * 6371000
    dy = math.radians(b[1] - a[1]) * 6371000
    return math.hypot(dx, dy)


def speed_of(p):
    ms = p.get("maxspeed")
    if ms:
        try:
            vals = [int(v) for v in str(ms).replace(";", "|").split("|") if v.strip().isdigit()]
            if vals:
                return sum(vals) / len(vals)
        except ValueError:
            pass
    return MAX_SPEEDS.get(p["highway"], 30)


def main(path):
    features = json.loads(Path(path).read_text())["features"]
    ways = []
    for f in features:
        p = f["properties"]
        if p.get("highway") not in DRIVE or f["geometry"]["type"] != "LineString":
            continue
        if p.get("access") in ("no", "private"):
            continue
        coords = [tuple(round(c, 7) for c in pt) for pt in f["geometry"]["coordinates"]]
        if not all(inside(*c) for c in coords):
            continue
        ow = str(p.get("oneway", "")).lower()
        if ow in ("yes", "true", "1"):
            direction = 1
        elif ow == "-1":
            direction = -1
        elif ow == "no":
            direction = 0
        else:
            direction = 1 if (p["highway"] == "motorway" or p.get("junction") in ("roundabout", "circular")) else 0
        ways.append({"coords": coords, "dir": direction, "name": p.get("name"), "hw": p["highway"], "speed": speed_of(p)})

    # A point is a graph node if it ends a way or is shared by more than one way segment.
    use = defaultdict(int)
    for w in ways:
        for i, c in enumerate(w["coords"]):
            use[c] += 1 if 0 < i < len(w["coords"]) - 1 else 2
    is_node = {c for c, n in use.items() if n >= 2}

    G = nx.DiGraph()
    for w in ways:
        cs = w["coords"]
        start = 0
        for i in range(1, len(cs)):
            if cs[i] in is_node:
                piece = cs[start:i + 1]
                length = sum(meters(piece[k], piece[k + 1]) for k in range(len(piece) - 1))
                attrs = dict(length=length, name=w["name"], hw=w["hw"], speed=w["speed"])
                if w["dir"] >= 0:
                    G.add_edge(piece[0], piece[-1], geom=piece[1:-1], **attrs)
                if w["dir"] <= 0:
                    G.add_edge(piece[-1], piece[0], geom=piece[1:-1][::-1], **attrs)
                start = i

    # keep the largest strongly connected component so every route exists
    comp = max(nx.strongly_connected_components(G), key=len)
    G = G.subgraph(comp).copy()
    # a node is a "major junction" if a major road passes through it
    major = {n for n in G if any(G.edges[e]["hw"] in MAJOR for e in list(G.in_edges(n)) + list(G.out_edges(n)))}

    nodes = list(G.nodes)
    idx = {n: i for i, n in enumerate(nodes)}
    lon0, lat0 = BBOX[0], BBOX[1]
    q = lambda c: [round((c[0] - lon0) * Q), round((c[1] - lat0) * Q)]
    names, name_idx = [], {}
    hws = sorted(MAX_SPEEDS)
    edges, geom = [], []
    for u, v, a in G.edges(data=True):
        nm = a["name"] or ""
        if nm not in name_idx:
            name_idx[nm] = len(names)
            names.append(nm)
        g0 = len(geom) // 2
        for c in a["geom"]:
            geom.extend(q(c))
        edges.extend([idx[u], idx[v], round(a["length"] * 10), round(a["speed"]), name_idx[nm], hws.index(a["hw"]), g0, len(a["geom"])])
    out = {
        "origin": [lon0, lat0], "scale": Q, "bbox": BBOX,
        "nodes": [x for n in nodes for x in q(n)],
        "major": [idx[n] for n in major],
        "edges": edges, "geom": geom, "names": names, "highways": hws,
        "attribution": "© OpenStreetMap contributors, ODbL",
    }
    dest = ROOT / "web" / "madrid.json"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps(out, separators=(",", ":"), ensure_ascii=False))
    print(f"{G.number_of_nodes():,} intersections, {G.number_of_edges():,} directed edges, {len(names):,} street names -> {dest} ({dest.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "madrid.geojson")
