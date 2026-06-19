import geopandas as gpd

BASE = r"C:\smartcity_final_exam"
oa = gpd.read_file(BASE + r"\data\processed\sgis\oa_merged.geojson")
oa_proj = oa.to_crs(epsg=5179)

pangyo = gpd.read_file(BASE + r"\data\processed\boundaries\pangyo_tv1_final.geojson").to_crs(epsg=5179)
cheongna = gpd.read_file(BASE + r"\data\processed\boundaries\cheongna_final2.geojson").to_crs(epsg=5179)

# intersects 기준으로 변경 (구역과 조금이라도 겹치면 포함)
oa_pg = gpd.sjoin(oa_proj, pangyo[['geometry']], how='inner', predicate='intersects').drop_duplicates('TOT_OA_CD')
oa_ch = gpd.sjoin(oa_proj, cheongna[['geometry']], how='inner', predicate='intersects').drop_duplicates('TOT_OA_CD')

print(f"판교: {len(oa_pg)}개, 청라: {len(oa_ch)}개")

# 구역계로 클리핑 (구역 밖으로 안 나가게)
oa_pg_clipped = gpd.clip(oa_pg, pangyo)
oa_ch_clipped = gpd.clip(oa_ch, cheongna)

oa_pg_clipped.to_crs(epsg=4326)[['TOT_OA_CD','pop','emp','biz','geometry']].to_file(
    r"C:\smartcity_final_exam\web\data\oa_pangyo_inner.geojson", driver="GeoJSON")
oa_ch_clipped.to_crs(epsg=4326)[['TOT_OA_CD','pop','emp','biz','geometry']].to_file(
    r"C:\smartcity_final_exam\web\data\oa_cheongna_inner.geojson", driver="GeoJSON")
print("저장 완료!")