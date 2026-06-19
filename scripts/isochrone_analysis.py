"""
등시간권 분석 스크립트
- 판교역(신분당선) / 청라국제도시역(공항철도) 기준
- 다익스트라로 전 역 최단시간 산출
- 30분·60분 등시간권 폴리곤 생성
- 등시간권 × SGIS 집계구 공간결합 → 도달 인구·종사자 산출
- 누적 접근성 곡선 데이터 생성

실행: python scripts/isochrone_analysis.py
"""

import pandas as pd
import numpy as np
import heapq
import json
import geopandas as gpd
from shapely.geometry import Point
from shapely.ops import unary_union
from pathlib import Path

# ── 경로 설정 ──────────────────────────────────────────────
BASE   = Path(r"C:\smartcity_final_exam")
SUBWAY = BASE / "data" / "raw" / "subway_network" / "network"
SGIS   = BASE / "data" / "processed" / "sgis" / "oa_merged.geojson"
OUT    = BASE / "data" / "processed" / "isochrone"
OUT.mkdir(parents=True, exist_ok=True)

# ── Step 1. 지하철 네트워크 로드 ───────────────────────────
print("Step 1. 지하철 네트워크 로드...")
nodes = pd.read_csv(SUBWAY / "nodes.tsv", sep="\t")
links = pd.read_csv(SUBWAY / "links.tsv", sep="\t")

# 2026-06-15 기준 운영 중인 노드/링크만
nodes = nodes[nodes['begin'] <= '2026-06-15'].copy()
links = links[links['begin'] <= '2026-06-15'].copy()
print(f"  유효 역: {len(nodes)}개, 유효 구간: {len(links)}개")

# ── Step 2. 그래프 구성 ────────────────────────────────────
print("Step 2. 그래프 구성...")
graph = {row['id']: [] for _, row in nodes.iterrows()}
for _, row in links.iterrows():
    f, t = row['fromNode'], row['toNode']
    if f in graph and t in graph:
        graph[f].append((t, row['timeFT']))
        graph[t].append((f, row['timeTF']))

# ── Step 3. 다익스트라 ────────────────────────────────────
def dijkstra(graph, start):
    dist = {node: float('inf') for node in graph}
    dist[start] = 0
    pq = [(0, start)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        for v, w in graph[u]:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                heapq.heappush(pq, (dist[v], v))
    return dist

# ── Step 4. 핵심역 정의 ───────────────────────────────────
# 판교역(신분당선) id=824, 청라국제도시역(공항철도) id=313
STATIONS = {
    "pangyo":   {"id": 824, "name": "판교역(신분당선)",    "label": "판교테크노밸리"},
    "cheongna": {"id": 313, "name": "청라국제도시역(공항철도)", "label": "청라국제업무·금융단지"},
}

# ── Step 5. 집계구 로드 ────────────────────────────────────
print("Step 5. 집계구 로드...")
oa = gpd.read_file(SGIS)
oa_proj = oa.to_crs(epsg=5179)

# ── Step 6. 분석 실행 ─────────────────────────────────────
all_results = {}

for key, info in STATIONS.items():
    print(f"\nStep 6. {info['name']} 분석 중...")
    dist = dijkstra(graph, info['id'])

    nodes_t = nodes.copy()
    nodes_t['travel_sec'] = nodes_t['id'].map(dist)
    nodes_t['travel_min'] = nodes_t['travel_sec'] / 60

    # 주요 역 소요시간 출력
    print("  주요 역 소요시간:")
    for nm in ['강남', '서울역', '홍대입구', '인천', '수원', '판교', '청라']:
        rows = nodes_t[nodes_t['statnm'].str.contains(nm, na=False)]
        if len(rows) > 0:
            best = rows['travel_min'].min()
            if best < float('inf'):
                print(f"    {nm}: {best:.0f}분")

    # 30분·60분 등시간권 역 GeoJSON 저장
    for t_limit in [30, 60]:
        r = nodes_t[nodes_t['travel_min'] <= t_limit].copy()
        gdf = gpd.GeoDataFrame(
            r,
            geometry=gpd.points_from_xy(r['lng'], r['lat']),
            crs="EPSG:4326"
        )
        gdf[['id','statnm','linenm','travel_min','geometry']].to_file(
            OUT / f"stations_{key}_{t_limit}min.geojson", driver="GeoJSON"
        )

    # 등시간권 폴리곤 생성 (역 500m 버퍼 합집합)
    print("  등시간권 폴리곤 생성...")
    for t_limit in [30, 60]:
        r = nodes_t[nodes_t['travel_min'] <= t_limit].copy()
        gdf = gpd.GeoDataFrame(
            r,
            geometry=gpd.points_from_xy(r['lng'], r['lat']),
            crs="EPSG:4326"
        ).to_crs(epsg=5179)

        poly = gdf.geometry.buffer(500).union_all()
        poly_gdf = gpd.GeoDataFrame(
            [{"key": key, "time_limit": t_limit, "n_stations": len(r)}],
            geometry=[poly],
            crs="EPSG:5179"
        ).to_crs(epsg=4326)
        poly_gdf.to_file(OUT / f"isochrone_{key}_{t_limit}min.geojson", driver="GeoJSON")

    # 누적 접근성 곡선 (5분 단위)
    print("  누적 접근성 곡선 계산...")
    cumulative = []
    for t in range(5, 65, 5):
        r = nodes_t[nodes_t['travel_min'] <= t].copy()
        if len(r) == 0:
            cumulative.append({"time": t, "n_stations": 0, "pop": 0, "emp": 0})
            continue

        gdf = gpd.GeoDataFrame(
            r,
            geometry=gpd.points_from_xy(r['lng'], r['lat']),
            crs="EPSG:4326"
        ).to_crs(epsg=5179)

        buffer = gdf.geometry.buffer(500).union_all()
        buffer_gdf = gpd.GeoDataFrame(geometry=[buffer], crs="EPSG:5179")
        oa_in = gpd.sjoin(oa_proj, buffer_gdf, how='inner', predicate='intersects')

        cumulative.append({
            "time": int(t),
            "n_stations": int(len(r)),
            "pop": int(oa_in['pop'].sum()),
            "emp": int(oa_in['emp'].sum()),
        })

    all_results[key] = {
        "station_name": info['name'],
        "label": info['label'],
        "cumulative": cumulative
    }

    df = pd.DataFrame(cumulative)
    print(f"\n  [{info['name']}] 누적 접근성:")
    print(df.to_string(index=False))

# ── Step 7. 결과 저장 ─────────────────────────────────────
with open(OUT / "isochrone_results.json", "w", encoding="utf-8") as f:
    json.dump(all_results, f, ensure_ascii=False, indent=2)

# CSV도 저장
for key, data in all_results.items():
    pd.DataFrame(data['cumulative']).to_csv(
        OUT / f"cumulative_{key}.csv", index=False, encoding="utf-8-sig"
    )

print("\n\n=== 최종 비교 수치 ===")
for key, data in all_results.items():
    df = pd.DataFrame(data['cumulative'])
    r30 = df[df['time']==30].iloc[0]
    r60 = df[df['time']==60].iloc[0]
    print(f"\n{data['station_name']}:")
    print(f"  30분: 역 {r30['n_stations']}개 / 인구 {r30['pop']:,}명 / 종사자 {r30['emp']:,}명")
    print(f"  60분: 역 {r60['n_stations']}개 / 인구 {r60['pop']:,}명 / 종사자 {r60['emp']:,}명")

print("\n전처리 완료! 출력 파일:", OUT)