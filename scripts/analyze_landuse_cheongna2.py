import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(r"C:\smartcity_final_exam")
OUT = BASE / "data" / "processed" / "landuse"

# 인천 용도지역 로드
gdf_ic = gpd.read_file(BASE / "data/raw/landuse/incheon/AL_D154_28_20260412.shp", encoding="euc-kr")

# 새 청라 구역계로 클리핑
cheongna = gpd.read_file(BASE / "data/processed/boundaries/cheongna_final2.geojson").to_crs(gdf_ic.crs)
landuse_cheongna = gpd.clip(gdf_ic, cheongna)

# 저장
landuse_cheongna.to_crs(epsg=4326).to_file(OUT / "landuse_cheongna2.geojson", driver="GeoJSON")
print(f"청라 용도지역 폴리곤 수: {len(landuse_cheongna)}")

# 용도지역 분석
YONGDO = [
    "제1종전용주거지역","제2종전용주거지역",
    "제1종일반주거지역","제2종일반주거지역","제3종일반주거지역",
    "준주거지역",
    "중심상업지역","일반상업지역","근린상업지역","유통상업지역",
    "전용공업지역","일반공업지역","준공업지역",
    "보전녹지지역","생산녹지지역","자연녹지지역",
]

def extract_yongdo(text):
    if pd.isna(text): return "미지정"
    s = str(text)
    for yd in YONGDO:
        if yd in s: return yd
    if "도로구역" in s or "하천구역" in s: return "도로·하천"
    if "특별계획구역" in s or "완충녹지" in s or "공공공지" in s: return "공공시설·녹지"
    return "기타"

landuse_cheongna = landuse_cheongna.copy()
landuse_cheongna["용도지역"] = landuse_cheongna["A8"].apply(extract_yongdo)
lc_proj = landuse_cheongna.to_crs(epsg=5179)
lc_proj["area_m2"] = lc_proj.geometry.area

total = lc_proj["area_m2"].sum()
result = lc_proj.groupby("용도지역")["area_m2"].sum().reset_index()
result["비율(%)"] = (result["area_m2"] / total * 100).round(1)
result = result.sort_values("비율(%)", ascending=False)

print("\n=== 청라 용도지역 (새 구역계) ===")
print(f"총 면적: {total:,.0f} m²")
print(result.to_string(index=False))

def lum_entropy(ratio_df):
    exclude = ["도로·하천","공공시설·녹지","기타","미지정"]
    df = ratio_df[~ratio_df["용도지역"].isin(exclude)].copy()
    p = df["비율(%)"] / df["비율(%)"].sum()
    p = p[p > 0]
    return -sum(p * np.log(p))

print(f"\nLUM 엔트로피: {lum_entropy(result):.4f}  (판교: 0.7485)")

result.to_csv(OUT / "cheongna_yongdo2.csv", index=False, encoding="utf-8-sig")
print("저장 완료!")