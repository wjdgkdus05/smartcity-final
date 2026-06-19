import pandas as pd
import geopandas as gpd
from pathlib import Path
import zipfile

BASE   = Path(r"C:\smartcity_final_exam")
RAW    = BASE / "data" / "raw" / "sgis"
BOUND  = BASE / "data" / "processed" / "boundaries"
OUT    = BASE / "data" / "processed" / "sgis"

# 산업분류 코드 매핑 (SGIS 10차 대분류)
INDUSTRY_MAP = {
    'cp_bem_001': 'A. 농림어업',
    'cp_bem_002': 'B. 광업',
    'cp_bem_003': 'C. 제조업',
    'cp_bem_004': 'D. 전기·가스·증기',
    'cp_bem_005': 'E. 수도·하수·폐기물',
    'cp_bem_006': 'F. 건설업',
    'cp_bem_007': 'G. 도·소매업',
    'cp_bem_008': 'H. 운수·창고업',
    'cp_bem_009': 'I. 숙박·음식점업',
    'cp_bem_010': 'J. 정보통신업',
    'cp_bem_011': 'K. 금융·보험업',
    'cp_bem_012': 'L. 부동산업',
    'cp_bem_013': 'M. 전문·과학·기술',
    'cp_bem_014': 'N. 사업시설관리',
    'cp_bem_015': 'O. 공공행정',
    'cp_bem_016': 'P. 교육서비스업',
    'cp_bem_017': 'Q. 보건·사회복지',
    'cp_bem_018': 'R. 예술·스포츠',
    'cp_bem_019': 'S. 협회·수리·개인',
}

# CSV 로드
TMP = RAW / "_tmp_industry"
def load_industry(sid):
    fname = TMP / f"{sid}_2023년_산업분류별(10차_대분류)_종사자수.csv"
    df = pd.read_csv(fname, encoding="euc-kr", header=None,
                     names=["year","TOT_OA_CD","industry_code","emp"],
                     dtype={"TOT_OA_CD":str,"industry_code":str})
    df["emp"] = pd.to_numeric(df["emp"], errors="coerce").fillna(0)
    return df

emp_all = pd.concat([load_industry(s) for s in ["11","23","31"]], ignore_index=True)
emp_all["industry"] = emp_all["industry_code"].map(INDUSTRY_MAP)

# 집계구 경계 로드
gdf_oa = gpd.read_file(BASE / "data/processed/sgis/oa_merged.geojson").to_crs(epsg=5179)

# 구역계 로드
pangyo   = gpd.read_file(BOUND / "pangyo_tv1_final.geojson").to_crs(epsg=5179)
cheongna = gpd.read_file(BOUND / "cheongna_final2.geojson").to_crs(epsg=5179)

# 구역 내 집계구 추출 (centroid 기준)
gdf_oa["centroid"] = gdf_oa.geometry.centroid
oa_pg = gdf_oa[gdf_oa["centroid"].within(pangyo.geometry.iloc[0])]["TOT_OA_CD"].tolist()
oa_ch = gdf_oa[gdf_oa["centroid"].within(cheongna.geometry.iloc[0])]["TOT_OA_CD"].tolist()

print(f"판교 집계구: {len(oa_pg)}개, 청라 집계구: {len(oa_ch)}개")

# 구역별 업종 집계
def get_industry_summary(oa_list, label):
    df = emp_all[emp_all["TOT_OA_CD"].isin(oa_list)]
    result = df.groupby("industry")["emp"].sum().reset_index()
    result["비율(%)"] = (result["emp"] / result["emp"].sum() * 100).round(1)
    result = result.sort_values("비율(%)", ascending=False)
    result["지역"] = label
    return result

pg_industry = get_industry_summary(oa_pg, "판교테크노밸리")
ch_industry = get_industry_summary(oa_ch, "청라국제업무·금융단지")

print("\n=== 판교테크노밸리 업종 구성 ===")
print(f"총 종사자: {pg_industry['emp'].sum():,.0f}명")
print(pg_industry[["industry","emp","비율(%)"]].to_string(index=False))

print("\n=== 청라국제업무·금융단지 업종 구성 ===")
print(f"총 종사자: {ch_industry['emp'].sum():,.0f}명")
print(ch_industry[["industry","emp","비율(%)"]].to_string(index=False))

# CSV 저장
pg_industry.to_csv(OUT / "industry_pangyo.csv", index=False, encoding="utf-8-sig")
ch_industry.to_csv(OUT / "industry_cheongna.csv", index=False, encoding="utf-8-sig")
print("\n저장 완료!")