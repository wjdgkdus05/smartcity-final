import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(r"C:\smartcity_final_exam")
WEB  = BASE / "web" / "data"

bld_pg = gpd.read_file(WEB / "bld_pangyo.geojson")
bld_ch = gpd.read_file(WEB / "bld_cheongna.geojson")

def calc_bld_lum(gdf):
    df = gdf[gdf["용도분류"].notna()].copy()
    total = df["연면적(㎡)"].sum()
    result = df.groupby("용도분류")["연면적(㎡)"].sum().reset_index()
    result["비율"] = result["연면적(㎡)"] / total
    p = result["비율"]
    p = p[p > 0]
    lum = -sum(p * np.log(p))
    return result, lum, total

pg_result, pg_lum, pg_total = calc_bld_lum(bld_pg)
ch_result, ch_lum, ch_total = calc_bld_lum(bld_ch)

print("=== 판교 건축물 주용도 기준 LUM ===")
print(f"총 연면적: {pg_total:,.0f}㎡")
print(pg_result.sort_values("비율", ascending=False).to_string(index=False))
print(f"LUM: {pg_lum:.4f}")

print("\n=== 청라 건축물 주용도 기준 LUM ===")
print(f"총 연면적: {ch_total:,.0f}㎡")
print(ch_result.sort_values("비율", ascending=False).to_string(index=False))
print(f"LUM: {ch_lum:.4f}")