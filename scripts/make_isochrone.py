import pandas as pd
import geopandas as gpd
import heapq
from shapely.ops import unary_union
from shapely.geometry import MultiPoint
from pathlib import Path

BASE   = Path(r"C:\smartcity_final_exam")
SUBWAY = BASE / "data" / "raw" / "subway_network" / "network"
OUT    = BASE / "data" / "processed" / "isochrone"

nodes = pd.read_csv(SUBWAY / "nodes.tsv", sep="\t")
links = pd.read_csv(SUBWAY / "links.tsv", sep="\t")
nodes = nodes[nodes['begin'] <= '2026-06-15'].copy()
links = links[links['begin'] <= '2026-06-15'].copy()

graph = {row['id']: [] for _, row in nodes.iterrows()}
for _, row in links.iterrows():
    f, t = row['fromNode'], row['toNode']
    if f in graph and t in graph:
        graph[f].append((t, row['timeFT']))
        graph[t].append((f, row['timeTF']))

def dijkstra(graph, start):
    dist = {node: float('inf') for node in graph}
    dist[start] = 0
    pq = [(0, start)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]: continue
        for v, w in graph[u]:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                heapq.heappush(pq, (dist[v], v))
    return dist

for key, station_id in [("pangyo", 824), ("cheongna", 313)]:
    dist = dijkstra(graph, station_id)
    nodes_t = nodes.copy()
    nodes_t['travel_min'] = nodes_t['id'].map(dist) / 60

    gdf = gpd.GeoDataFrame(
        nodes_t,
        geometry=gpd.points_from_xy(nodes_t['lng'], nodes_t['lat']),
        crs="EPSG:4326"
    ).to_crs(epsg=5179)

    for minutes in [30, 60]:
        r = gdf[gdf['travel_min'] <= minutes].copy()
        # Concave Hull - 역 위치를 자연스럽게 감싸는 폴리곤
        buf = r.geometry.buffer(3000)  # 각 역 3km 버퍼
        poly = unary_union(buf)
        
        result = gpd.GeoDataFrame(
            [{"key": key, "minutes": minutes, "n_stations": len(r)}],
            geometry=[poly], crs="EPSG:5179"
        ).to_crs(epsg=4326)
        
        result.to_file(OUT / f"isochrone_{key}_{minutes}min.geojson", driver="GeoJSON")
        print(f"{key} {minutes}분: {len(r)}개 역, 저장 완료")