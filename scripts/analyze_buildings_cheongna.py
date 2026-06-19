import pandas as pd
import geopandas as gpd

ldreg_ch = gpd.read_file(r"C:\smartcity_final_exam\data\raw\boundaries\incheon\LSMD_CONT_LDREG_28260_202605.shp", encoding="euc-kr")
bld_ch = pd.read_csv(r"C:\smartcity_final_exam\data\raw\buildings\bld_cheongna.csv", encoding="utf-8-sig")
bld_ch = bld_ch[bld_ch['주부속구분코드'] == 0].copy()

def make_pnu(row):
    sgg = str(int(row['시군구코드'])).zfill(5)
    dong = str(int(row['법정동코드'])).zfill(5)
    gb = '1' if int(row['대지구분코드']) == 0 else '2'
    bon = str(int(row['번'])).zfill(4)
    bu = str(int(row['지'])).zfill(4)
    return sgg + dong + gb + bon + bu

bld_ch['PNU'] = bld_ch.apply(make_pnu, axis=1)
ldreg_j = ldreg_ch.merge(bld_ch[['PNU','건물명','주용도코드명','연면적(㎡)','용적률(%)']], on='PNU', how='left')

cheongna = gpd.read_file(r"C:\smartcity_final_exam\data\processed\boundaries\cheongna_final2.geojson").to_crs(ldreg_ch.crs)
ch_clip = gpd.sjoin(ldreg_j, cheongna[['geometry']], how='inner', predicate='intersects')
bld_only = ch_clip[ch_clip['주용도코드명'].notna()].copy()

# 오피스텔 vs 순수업무 분리
오피스텔키워드 = ['오피스텔', '큐브시그니처', '골드클래스', '스위트클래스', '센트럴시티',
              '스너그시티', '레이크원', '디에스틴', '레이크 봄', '리베라움', '더레이크',
              '월드메르디앙', '디오스텔']

def classify_detail(row):
    name = str(row['건물명']) if pd.notna(row['건물명']) else ''
    yongdo = str(row['주용도코드명']) if pd.notna(row['주용도코드명']) else ''
    if any(k in name for k in 오피스텔키워드):
        return "업무시설(오피스텔-실질주거)"
    if yongdo == '업무시설':
        return "업무시설(순수)"
    if '근린생활' in yongdo:
        return "근린생활"
    if '판매' in yongdo:
        return "판매·상업"
    return "기타"

bld_only['용도분류상세'] = bld_only.apply(classify_detail, axis=1)

total = bld_only['연면적(㎡)'].sum()
result = bld_only.groupby('용도분류상세')['연면적(㎡)'].sum().reset_index()
result['비율(%)'] = (result['연면적(㎡)'] / total * 100).round(1)
result = result.sort_values('비율(%)', ascending=False)

print("=== 청라 건축물 상세 용도 (연면적 기준) ===")
print(f"총 연면적: {total:,.0f} ㎡  |  건축물 수: {len(bld_only)}동")
print(result.to_string(index=False))

print("\n=== 판교와 비교 ===")
print(f"판교 순수업무 비율: 34.3%")
ch_pure = result[result['용도분류상세']=='업무시설(순수)']['비율(%)'].sum()
ch_ofi = result[result['용도분류상세']=='업무시설(오피스텔-실질주거)']['비율(%)'].sum()
print(f"청라 순수업무 비율: {ch_pure:.1f}%")
print(f"청라 오피스텔(실질주거) 비율: {ch_ofi:.1f}%")