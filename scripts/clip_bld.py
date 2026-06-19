import geopandas as gpd
from pathlib import Path

BASE  = Path(r"C:\smartcity_final_exam")
BOUND = BASE / "data" / "processed" / "boundaries"
OUT   = BASE / "data" / "processed" / "landuse"
WEB   = BASE / "web" / "data"

pangyo   = gpd.read_file(BOUND / "pangyo_tv1_final.geojson").to_crs(epsg=5179)
cheongna = gpd.read_file(BOUND / "cheongna_final2.geojson").to_crs(epsg=5179)

for fname, zone, label in [
    ("bld_pangyo.geojson",   pangyo,   "판교"),
    ("bld_cheongna.geojson", cheongna, "청라"),
]:
    gdf = gpd.read_file(WEB / fname).to_crs(epsg=5179)
    clipped = gpd.clip(gdf, zone).to_crs(epsg=4326)
    clipped.to_file(WEB / fname, driver="GeoJSON")
    print(f"{label}: {len(gdf)} → {len(clipped)} 필지 (클리핑 완료)")