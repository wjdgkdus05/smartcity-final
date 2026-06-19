import geopandas as gpd
import pandas as pd
from pathlib import Path

BASE = Path(r"C:\smartcity_final_exam")
LANDUSE = BASE / "data" / "raw" / "landuse"
BOUND = BASE / "data" / "processed" / "boundaries"
OUT = BASE / "data" / "processed" / "landuse"
OUT.mkdir(parents=True, exist_ok=True)

# 경기도 SHP 여러 개 합치기
print("경기도 용도지역 로드 중...")
gg_files = list((LANDUSE / "gyeonggi").glob("AL_D154_41_*.shp"))
gg_files = [f for f in gg_files if f.parent == LANDUSE / "gyeonggi"]
print(f"  파일 수: {len(gg_files)}개")
gdf_gg = pd.concat([gpd.read_file(f, encoding="euc-kr") for f in gg_files], ignore_index=True)
gdf_gg = gpd.GeoDataFrame(gdf_gg, crs=gpd.read_file(gg_files[0]).crs)

# 인천 SHP 로드
print("인천 용도지역 로드 중...")
ic_file = LANDUSE / "incheon" / "AL_D154_28_20260412.shp"
gdf_ic = gpd.read_file(ic_file, encoding="euc-kr")

print(f"경기 행수: {len(gdf_gg):,}")
print(f"인천 행수: {len(gdf_ic):,}")
print(f"컬럼: {gdf_gg.columns.tolist()}")

# 구역계 로드
pangyo = gpd.read_file(BOUND / "pangyo_tv1_final.geojson").to_crs(gdf_gg.crs)
cheongna = gpd.read_file(BOUND / "cheongna_ibd_final.geojson").to_crs(gdf_ic.crs)

# 구역계로 클리핑
print("\n클리핑 중...")
landuse_pangyo = gpd.clip(gdf_gg, pangyo)
landuse_cheongna = gpd.clip(gdf_ic, cheongna)

print(f"판교 용도지역 폴리곤 수: {len(landuse_pangyo)}")
print(f"청라 용도지역 폴리곤 수: {len(landuse_cheongna)}")
print(f"\n판교 용도지역 종류:\n{landuse_pangyo.iloc[:,2:6].head()}")

# 저장
landuse_pangyo.to_crs(epsg=4326).to_file(OUT / "landuse_pangyo.geojson", driver="GeoJSON")
landuse_cheongna.to_crs(epsg=4326).to_file(OUT / "landuse_cheongna.geojson", driver="GeoJSON")
print("\n저장 완료!")