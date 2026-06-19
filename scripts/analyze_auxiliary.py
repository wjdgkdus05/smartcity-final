import geopandas as gpd
import pandas as pd
from pathlib import Path

BASE   = Path(r"C:\smartcity_final_exam")
BOUND  = BASE / "data" / "processed" / "boundaries"
SUBWAY = BASE / "data" / "raw" / "subway_network" / "network"
OUT    = BASE / "data" / "processed" / "auxiliary"

pangyo   = gpd.read_file(BOUND / "pangyo_tv1_final.geojson").to_crs(epsg=5179)
cheongna = gpd.read_file(BOUND / "cheongna_final2.geojson").to_crs(epsg=5179)

nodes = pd.read_csv(SUBWAY / "nodes.tsv", sep="\t")
nodes = nodes[nodes['begin'] <= '2026-06-15'].copy()
gdf_nodes = gpd.GeoDataFrame(
    nodes,
    geometry=gpd.points_from_xy(nodes['lng'], nodes['lat']),
    crs="EPSG:4326"
).to_crs(epsg=5179)

# 핵심역 직접 지정 (판교역 신분당선=824, 청라국제도시역=313)
for label, zone, station_id in [("판교", pangyo, 824), ("청라", cheongna, 313)]:
    zone_area = zone.geometry.area.iloc[0]
    station = gdf_nodes[gdf_nodes['id'] == station_id].copy()

    print(f"\n=== {label} ===")
    print(f"구역 면적: {zone_area:,.0f} m²")

    for radius in [500, 1000]:
        # 핵심역 버퍼
        buf = station.geometry.buffer(radius).union_all()
        # 구역과 교차
        clipped = buf.intersection(zone.geometry.iloc[0])
        ratio = clipped.area / zone_area * 100

        # 핵심역까지 거리
        dist = station.geometry.distance(zone.geometry.centroid.iloc[0]).iloc[0]

        print(f"  역세권({radius}m) 구역 내 면적 비율: {ratio:.1f}%")
        print(f"  핵심역-구역 중심 거리: {dist:.0f}m")

        gpd.GeoDataFrame(
            [{"label": label, "radius": radius, "ratio": round(ratio,1)}],
            geometry=[clipped],
            crs="EPSG:5179"
        ).to_crs(epsg=4326).to_file(
            OUT / f"station_buffer_{label}_{radius}m.geojson", driver="GeoJSON"
        )

print("\n완료!")