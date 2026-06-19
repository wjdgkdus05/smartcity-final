import geopandas as gpd
import pandas as pd
from pathlib import Path

BASE  = Path(r"C:\smartcity_final_exam")
BOUND = BASE / "data" / "processed" / "boundaries"
WEB   = BASE / "web" / "data"

ldreg_pg = gpd.read_file(BASE / "data/raw/boundaries/gyeonggi/LSMD_CONT_LDREG_41135_202605.shp", encoding="euc-kr")
ldreg_ch = gpd.read_file(BASE / "data/raw/boundaries/incheon/LSMD_CONT_LDREG_28260_202605.shp", encoding="euc-kr")

bld_pg = pd.read_csv(BASE / "data/raw/buildings/bld_pangyo.csv", encoding="utf-8-sig")
bld_ch = pd.read_csv(BASE / "data/raw/buildings/bld_cheongna.csv", encoding="utf-8-sig")
bld_pg = bld_pg[bld_pg['주부속구분코드']==0].copy()
bld_ch = bld_ch[bld_ch['주부속구분코드']==0].copy()

def make_pnu(row):
    sgg=str(int(row['시군구코드'])).zfill(5)
    dong=str(int(row['법정동코드'])).zfill(5)
    gb='1' if int(row['대지구분코드'])==0 else '2'
    bon=str(int(row['번'])).zfill(4)
    bu=str(int(row['지'])).zfill(4)
    return sgg+dong+gb+bon+bu

오피스텔키워드=['오피스텔','큐브시그니처','골드클래스','스위트클래스','센트럴시티','스너그시티','레이크원','디에스틴','레이크 봄','리베라움','더레이크','월드메르디앙','디오스텔']

def classify(row):
    name=str(row['건물명']) if pd.notna(row.get('건물명')) else ''
    yongdo=str(row['주용도코드명']) if pd.notna(row.get('주용도코드명')) else ''
    if any(k in name for k in 오피스텔키워드): return '업무(오피스텔)'
    if '업무시설' in yongdo: return '업무(순수)'
    if '교육연구' in yongdo: return '교육연구'
    if '근린생활' in yongdo: return '근린생활'
    if '판매' in yongdo: return '판매·상업'
    if any(x in yongdo for x in ['단독주택','공동주택']): return '주거'
    if '주차' in yongdo or '자동차' in yongdo: return '주차·교통'
    if pd.isna(row.get('주용도코드명')): return None
    return '기타'

bld_pg['PNU'] = bld_pg.apply(make_pnu, axis=1)
bld_ch['PNU'] = bld_ch.apply(make_pnu, axis=1)
bld_pg['용도분류'] = bld_pg.apply(classify, axis=1)
bld_ch['용도분류'] = bld_ch.apply(classify, axis=1)

pangyo   = gpd.read_file(BOUND / "pangyo_tv1_final.geojson").to_crs(ldreg_pg.crs)
cheongna = gpd.read_file(BOUND / "cheongna_final2.geojson").to_crs(ldreg_ch.crs)

for bld, ldreg, zone, fname in [
    (bld_pg, ldreg_pg, pangyo,   "bld_pangyo.geojson"),
    (bld_ch, ldreg_ch, cheongna, "bld_cheongna.geojson"),
]:
    cols = ['PNU','건물명','주용도코드명','용도분류','연면적(㎡)','용적률(%)']
    cols = [c for c in cols if c in bld.columns]
    joined = ldreg.merge(bld[cols], on='PNU', how='left')
    clipped = gpd.clip(gpd.sjoin(joined, zone[['geometry']], how='inner', predicate='intersects').drop_duplicates('PNU'), zone)
    clipped.to_crs(epsg=4326)[['PNU','건물명','용도분류','연면적(㎡)','용적률(%)','geometry']].to_file(WEB/fname, driver="GeoJSON")
    print(f"{fname} 저장 완료: {len(clipped)}필지")