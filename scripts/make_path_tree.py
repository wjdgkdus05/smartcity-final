import pandas as pd
import geopandas as gpd
import heapq
from shapely.geometry import LineString
from pathlib import Path

BASE   = Path(r"C:\smartcity_final_exam")
SUBWAY = BASE / "data" / "raw" / "subway_network" / "network"
OUT    = BASE / "data" / "processed" / "isochrone"

nodes = pd.read_csv(SUBWAY / "nodes.tsv", sep="\t")
links = pd.read_csv(SUBWAY / "links.tsv", sep="\t")
nodes = nodes[nodes['begin'] <= '2026-06-15'].copy()
links = links[links['begin'] <= '2026-06-15'].copy()

# 노드 좌표 딕셔너리
coord = {row['id']: (row['lng'], row['lat']) for _, row in nodes.iterrows()}

# 그래프 구성 (링크 ID도 저장)
graph = {row['id']: [] for _, row in nodes.iterrows()}
for _, row in links.iterrows():
    f, t = row['fromNode'], row['toNode']
    if f in graph and t in graph:
        graph[f].append((t, row['timeFT']))
        graph[t].append((f, row['timeTF']))

# 다익스트라 + 이전 노드 추적
def dijkstra_prev(graph, start):
    dist = {node: float('inf') for node in graph}
    prev = {node: None for node in graph}
    dist[start] = 0
    pq = [(0, start)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]: continue
        for v, w in graph[u]:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                prev[v] = u
                heapq.heappush(pq, (dist[v], v))
    return dist, prev

# 최단경로 트리 → 링크 세그먼트 생성
def make_path_lines(start_id, prev, dist, max_min, nodes_df):
    node_dict = nodes_df.set_index('id').to_dict('index')
    lines = []
    for node_id, p in prev.items():
        if p is None: continue
        if dist[node_id] / 60 > max_min: continue
        if node_id not in coord or p not in coord: continue
        lines.append({
            'from_id': p,
            'to_id': node_id,
            'travel_min': dist[node_id] / 60,
            'statnm': node_dict.get(node_id, {}).get('statnm', ''),
            'linenm': node_dict.get(node_id, {}).get('linenm', ''),
            'geometry': LineString([coord[p], coord[node_id]])
        })
    return lines

for key, station_id in [("pangyo", 824), ("cheongna", 313)]:
    dist, prev = dijkstra_prev(graph, station_id)
    
    for minutes in [30, 60]:
        lines = make_path_lines(station_id, prev, dist, minutes, nodes)
        gdf = gpd.GeoDataFrame(lines, crs="EPSG:4326")
        
        # 시간대별 색상 컬럼 추가
        def time_color(t):
            if t <= 10: return '#00E5FF'
            elif t <= 20: return '#00BFA5'
            elif t <= 30: return '#FFD600'
            elif t <= 45: return '#FF6D00'
            else: return '#FF1744'
        gdf['color'] = gdf['travel_min'].apply(time_color)
        
        out_path = OUT / f"path_tree_{key}_{minutes}min.geojson"
        gdf.to_file(out_path, driver="GeoJSON")
        print(f"{key} {minutes}분: {len(gdf)}개 경로선 저장")