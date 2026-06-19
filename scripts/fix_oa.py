import geopandas as gpd

oa = gpd.read_file(r"C:\smartcity_final_exam\data\processed\sgis\oa_merged.geojson")
oa_proj = oa.to_crs(epsg=5179)

pangyo   = gpd.read_file(r"C:\smartcity_final_exam\data\processed\boundaries\pangyo_tv1_final.geojson").to_crs(epsg=5179)
cheongna = gpd.read_file(r"C:\smartcity_final_exam\data\processed\boundaries\cheongna_final2.geojson").to_crs(epsg=5179)

# centroid 기준으로 집계구 선택 후 구역계로 클리핑
oa_proj['centroid_geom'] = oa_proj.geometry.centroid
oa_pg = oa_proj[oa_proj['centroid_geom'].within(pangyo.geometry.iloc[0])].copy()
oa_ch = oa_proj[oa_proj['centroid_geom'].within(cheongna.geometry.iloc[0])].copy()

# 구역계로 클리핑 (삐져나온 부분 제거)
oa_pg_clipped = gpd.clip(oa_pg.drop('centroid_geom',axis=1), pangyo)
oa_ch_clipped = gpd.clip(oa_ch.drop('centroid_geom',axis=1), cheongna)

print(f"판교: {len(oa_pg_clipped)}개, 청라: {len(oa_ch_clipped)}개")

oa_pg_clipped.to_crs(epsg=4326)[['TOT_OA_CD','pop','emp','biz','geometry']].to_file(
    r"C:\smartcity_final_exam\web\data\oa_pangyo_inner.geojson", driver="GeoJSON")
oa_ch_clipped.to_crs(epsg=4326)[['TOT_OA_CD','pop','emp','biz','geometry']].to_file(
    r"C:\smartcity_final_exam\web\data\oa_cheongna_inner.geojson", driver="GeoJSON")
print("저장 완료!")