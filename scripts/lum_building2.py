import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(r"C:\smartcity_final_exam")
WEB  = BASE / "web" / "data"

bld_pg = gpd.read_file(WEB / "bld_pangyo.geojson")
bld_ch = gpd.read_file(WEB / "bld_cheongna.geojson")

def reclassify(yongdo):
    if yongdo == "업무(오피스텔)":
        return "주거"
    return yongdo

bld_pg["용도_실질"] = bld_pg["용도분류"].apply(reclassify)
bld_ch["용도_실질"] = bld_ch["용도분류"].apply(reclassify)

def calc_bld_lum(gdf, label):
    df = gdf[gdf["용도_실질"].notna()].copy()
    df["연면적(㎡)"] = pd.to_numeric(df["연면적(㎡)"], errors="coerce")
    total = df["연면적(㎡)"].sum()

    # groupby로 명시적 재합산
    grouped = df.groupby("용도_실질", as_index=False)["연면적(㎡)"].sum()
    grouped["비율"] = grouped["연면적(㎡)"] / total
    grouped = grouped.sort_values("비율", ascending=False)

    p = grouped["비율"].values
    p = p[p > 0]
    lum = -np.sum(p * np.log(p))

    print(f"\n=== {label} ===")
    print(grouped.to_string(index=False))
    print(f"총 연면적: {total:,.0f}㎡")
    print(f"LUM: {lum:.4f}")
    return lum

pg_lum = calc_bld_lum(bld_pg, "판교 (오피스텔→주거 통합)")
ch_lum = calc_bld_lum(bld_ch, "청라 (오피스텔→주거 통합)")