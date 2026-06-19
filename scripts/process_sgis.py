"""
SGIS 집계구 데이터 전처리 스크립트
- 집계구 경계 SHP + 인구·종사자·사업체 CSV 결합
- 판교·청라 구역계와 공간 결합하여 구역 내 통계 산출
- 출력: data/processed/sgis/

데이터 출처:
  - 집계구 경계: SGIS 통계지리정보서비스 (2025년 2분기)
  - 인구: SGIS 집계구별 통계(인구) 2024년
  - 종사자·사업체: SGIS 집계구별 통계(사업체) 2023년

실행: python scripts/process_sgis.py
"""

import pandas as pd
import geopandas as gpd
import zipfile, os
from pathlib import Path

# ── 경로 설정 ──────────────────────────────────────────────
BASE    = Path(r"C:\smartcity_final_exam")
RAW     = BASE / "data" / "raw" / "sgis"
BOUND   = BASE / "data" / "processed" / "boundaries"
OUT     = BASE / "data" / "processed" / "sgis"
OUT.mkdir(parents=True, exist_ok=True)

TMP = RAW / "_tmp"
TMP.mkdir(exist_ok=True)

# ── Step 1. 집계구 경계 SHP 압축 풀기 ──────────────────────
print("Step 1. 집계구 경계 압축 풀기...")
for sid in ["11", "23", "31"]:
    zf = next(RAW.glob(f"bnd_oa_{sid}_*.zip"))
    out_dir = TMP / f"shp_{sid}"
    out_dir.mkdir(exist_ok=True)
    with zipfile.ZipFile(zf) as z:
        z.extractall(out_dir)
    print(f"  {sid} 완료")

# ── Step 2. 집계구 경계 합치기 ──────────────────────────────
print("\nStep 2. 집계구 경계 합치기...")
gdfs = []
for sid in ["11", "23", "31"]:
    gdf = gpd.read_file(TMP / f"shp_{sid}", encoding="euc-kr")
    gdfs.append(gdf)
gdf_all = pd.concat(gdfs, ignore_index=True)
gdf_all = gpd.GeoDataFrame(gdf_all, crs=gdfs[0].crs)
gdf_all = gdf_all.drop_duplicates(subset="TOT_OA_CD")
print(f"  총 집계구: {len(gdf_all):,}개")

# ── Step 3. 통계 CSV 로드 ──────────────────────────────────
print("\nStep 3. 통계 CSV 로드...")
census_zip = next(RAW.glob("_census_reqdoc_*.zip"))
with zipfile.ZipFile(census_zip) as z:
    z.extractall(TMP / "csv")

def load_csv(fpath, col_name):
    df = pd.read_csv(fpath, encoding="euc-kr", header=None,
                     names=["year", "TOT_OA_CD", "item", col_name],
                     dtype={"TOT_OA_CD": str})
    return df[["TOT_OA_CD", col_name]]

csv_dir = TMP / "csv"

pop = pd.concat([
    load_csv(csv_dir / f"{sid}_2024년_인구총괄(총인구).csv", "pop")
    for sid in ["11", "23", "31"]
]).groupby("TOT_OA_CD", as_index=False)["pop"].sum()

emp = pd.concat([
    load_csv(csv_dir / f"{sid}_2023년_산업분류별(10차_대분류)_총괄종사자수.csv", "emp")
    for sid in ["11", "23", "31"]
]).groupby("TOT_OA_CD", as_index=False)["emp"].sum()

biz = pd.concat([
    load_csv(csv_dir / f"{sid}_2023년_산업분류별(10차_대분류)_총괄사업체수.csv", "biz")
    for sid in ["11", "23", "31"]
]).groupby("TOT_OA_CD", as_index=False)["biz"].sum()

print(f"  인구: {len(pop):,}개 집계구")
print(f"  종사자: {len(emp):,}개 집계구")

# ── Step 4. 결합 ────────────────────────────────────────────
print("\nStep 4. 경계 + 통계 결합...")
gdf = gdf_all.merge(pop, on="TOT_OA_CD", how="left")
gdf = gdf.merge(emp, on="TOT_OA_CD", how="left")
gdf = gdf.merge(biz, on="TOT_OA_CD", how="left")
gdf[["pop","emp","biz"]] = gdf[["pop","emp","biz"]].fillna(0).astype(int)

# WGS84 변환
gdf_wgs = gdf.to_crs(epsg=4326)
gdf_wgs.to_file(OUT / "oa_merged.geojson", driver="GeoJSON")
print(f"  저장: {OUT / 'oa_merged.geojson'}")

# ── Step 5. 구역계 × 집계구 공간 결합 ──────────────────────
print("\nStep 5. 구역 내 통계 산출...")
gdf_proj = gdf.to_crs(epsg=5179)

for name, fname in [("판교테크노밸리", "pangyo_tv1_final.geojson"),
                     ("청라국제업무단지", "cheongna_ibd_final.geojson")]:
    zone = gpd.read_file(BOUND / fname).to_crs(epsg=5179)
    oa_in = gpd.sjoin(gdf_proj, zone, how="inner", predicate="intersects")

    total_pop = oa_in["pop"].sum()
    total_emp = oa_in["emp"].sum()
    total_biz = oa_in["biz"].sum()
    jikjubi = total_emp / max(total_pop, 1)

    print(f"\n  [{name}]")
    print(f"    집계구 수: {len(oa_in)}개")
    print(f"    총 인구:   {total_pop:,}명  (2024)")
    print(f"    총 종사자: {total_emp:,}명  (2023)")
    print(f"    총 사업체: {total_biz:,}개  (2023)")
    print(f"    직주비:    {jikjubi:.2f}")

print("\n전처리 완료!")