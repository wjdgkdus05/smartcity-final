import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(r"C:\smartcity_final_exam")
OUT  = BASE / "data" / "processed" / "landuse"

lu_pg = gpd.read_file(OUT / "landuse_pangyo.geojson")
lu_ch = gpd.read_file(OUT / "landuse_cheongna.geojson")

YONGDO = [
    "제1종전용주거지역", "제2종전용주거지역",
    "제1종일반주거지역", "제2종일반주거지역", "제3종일반주거지역",
    "준주거지역",
    "중심상업지역", "일반상업지역", "근린상업지역", "유통상업지역",
    "전용공업지역", "일반공업지역", "준공업지역",
    "보전녹지지역", "생산녹지지역", "자연녹지지역",
    "관리지역", "농림지역", "자연환경보전지역",
]

def extract_yongdo(text):
    if pd.isna(text):
        return "미지정"
    s = str(text)
    for yd in YONGDO:
        if yd in s:
            return yd
    if "도로구역" in s or "하천구역" in s:
        return "도로·하천"
    if "특별계획구역" in s or "완충녹지" in s or "공공공지" in s or "유통및공급시설" in s:
        return "공공시설·녹지"
    return "기타"

lu_pg["용도지역"] = lu_pg["A8"].apply(extract_yongdo)
lu_ch["용도지역"] = lu_ch["A8"].apply(extract_yongdo)

lu_pg_proj = lu_pg.to_crs(epsg=5179)
lu_ch_proj = lu_ch.to_crs(epsg=5179)
lu_pg_proj["area_m2"] = lu_pg_proj.geometry.area
lu_ch_proj["area_m2"] = lu_ch_proj.geometry.area

def calc_ratio(gdf):
    total = gdf["area_m2"].sum()
    result = gdf.groupby("용도지역")["area_m2"].sum().reset_index()
    result["비율(%)"] = (result["area_m2"] / total * 100).round(1)
    return result.sort_values("비율(%)", ascending=False), total

pg_ratio, pg_total = calc_ratio(lu_pg_proj)
ch_ratio, ch_total = calc_ratio(lu_ch_proj)

print("=== 판교테크노밸리 용도지역 ===")
print(f"총 면적: {pg_total:,.0f} m²")
print(pg_ratio.to_string(index=False))

print("\n=== 청라국제업무단지 용도지역 ===")
print(f"총 면적: {ch_total:,.0f} m²")
print(ch_ratio.to_string(index=False))

# LUM 엔트로피 (도로·하천·공공시설 제외)
def lum_entropy(ratio_df):
    exclude = ["도로·하천", "공공시설·녹지", "기타", "미지정"]
    df = ratio_df[~ratio_df["용도지역"].isin(exclude)].copy()
    p = df["비율(%)"] / df["비율(%)"].sum()
    p = p[p > 0]
    return -sum(p * np.log(p))

print(f"\n=== LUM 엔트로피 (도로·하천·공공시설 제외) ===")
print(f"판교: {lum_entropy(pg_ratio):.4f}")
print(f"청라: {lum_entropy(ch_ratio):.4f}")

# 저장
pg_ratio.to_csv(OUT / "pangyo_yongdo.csv", index=False, encoding="utf-8-sig")
ch_ratio.to_csv(OUT / "cheongna_yongdo.csv", index=False, encoding="utf-8-sig")
print("\nCSV 저장 완료!")