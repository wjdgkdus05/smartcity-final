import geopandas as gpd
from pathlib import Path

OUT = Path(r"C:\smartcity_final_exam\data\processed\landuse")

# 판교 용도지역 확인
gdf = gpd.read_file(OUT / "landuse_pangyo.geojson")
print(f"판교 피처 수: {len(gdf)}")
print(f"A8 컬럼 있음: {'A8' in gdf.columns}")
if 'A8' in gdf.columns:
    print(gdf['A8'].value_counts().head(5))