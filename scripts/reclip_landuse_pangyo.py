import pandas as pd
import geopandas as gpd
from pathlib import Path

BASE = Path(r"C:\smartcity_final_exam")
OUT  = BASE / "data" / "processed" / "landuse"
BOUND = BASE / "data" / "processed" / "boundaries"

# 경기도 용도지역 SHP 다시 로드
gg_files = list((BASE / "data/raw/landuse/gyeonggi").glob("AL_D154_41_*.shp"))
gdf_gg = gpd.GeoDataFrame(pd.concat([gpd.read_file(f, encoding="euc-kr") for f in gg_files], ignore_index=True))
gdf_gg = gdf_gg.set_crs(gpd.read_file(gg_files[0]).crs)

# 새 판교 구역계로 클리핑
pangyo = gpd.read_file(BOUND / "pangyo_tv1_final.geojson").to_crs(gdf_gg.crs)
landuse_pangyo = gpd.clip(gdf_gg, pangyo)

landuse_pangyo.to_crs(epsg=4326).to_file(OUT / "landuse_pangyo.geojson", driver="GeoJSON")
print(f"판교 용도지역 재클리핑 완료: {len(landuse_pangyo)}개 필지")

import geopandas as gpd
total_area = landuse_pangyo.to_crs(epsg=5179).geometry.area.sum()
print(f"총 면적: {total_area:,.0f} m²")