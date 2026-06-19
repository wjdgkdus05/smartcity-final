import geopandas as gpd
from shapely.ops import unary_union

gdf = gpd.read_file(r"C:\smartcity_final_exam\data\processed\boundaries\pangyo_tv1_final.geojson")

merged = unary_union(gdf.geometry)
result = gpd.GeoDataFrame(
    [{"name": "판교테크노밸리"}],
    geometry=[merged],
    crs=gdf.crs
)
result.to_file(r"C:\smartcity_final_exam\data\processed\boundaries\pangyo_tv1_final.geojson", driver="GeoJSON")

print(f"병합 완료! 피처 수: {len(result)}")
print(f"면적: {result.to_crs(epsg=5179).geometry.area.sum():,.0f} m²")
print(f"geometry type: {result.geometry.type.iloc[0]}")