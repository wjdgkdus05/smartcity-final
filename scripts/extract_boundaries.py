"""
구역계 추출 스크립트
출처: 토지이음 지구단위계획구역 SHP (지구단위계획구역_20260513_전국.zip)
기준일: 2026-05-13
실행: python extract_boundaries.py
"""

import zipfile
import geopandas as gpd
from pathlib import Path

# ── 경로 설정 ──────────────────────────────────────────────
BASE = Path(r"C:\smartcity_final_exam")
RAW  = BASE / "data" / "raw" / "boundaries"
OUT  = BASE / "data" / "processed" / "boundaries"
ZIP  = RAW / "지구단위계획구역_20260513_전국.zip"

OUT.mkdir(parents=True, exist_ok=True)
TMP = RAW / "_tmp"
TMP.mkdir(exist_ok=True)

# ── 압축 풀기 ──────────────────────────────────────────────
print("압축 풀기 중...")
with zipfile.ZipFile(ZIP, "r") as z:
    # 41000=경기도(판교), 28000=인천(청라)
    for name in z.namelist():
        if "41000" in name or "28000" in name:
            z.extract(name, TMP)

# 경기도·인천 내부 zip 추가로 풀기
import zipfile as zf
for inner in TMP.glob("*.zip"):
    with zf.ZipFile(inner) as z2:
        z2.extractall(TMP / inner.stem)

# ── 판교 추출 ──────────────────────────────────────────────
print("판교 구역계 추출 중...")
gg_shp = TMP / "KLIP_005_20260501_41000" / "KLIP_C_UQ161.shp"
gdf_gg = gpd.read_file(gg_shp, encoding="euc-kr")
pangyo = gdf_gg[gdf_gg["remark"] == "판교"].copy()
pangyo_wgs = pangyo.to_crs(epsg=4326)
pangyo_wgs.to_file(OUT / "pangyo_boundary.geojson", driver="GeoJSON")

area_pangyo = float(pangyo["dgm_ar"].iloc[0])
print(f"  → 판교 면적: {area_pangyo:,.0f} m²  ({area_pangyo/1_000_000:.2f} km²)")
print(f"  → 저장: {OUT / 'pangyo_boundary.geojson'}")

# ── 청라 추출 ──────────────────────────────────────────────
print("청라 구역계 추출 중...")
ic_shp = TMP / "KLIP_005_20260501_28000" / "KLIP_C_UQ161.shp"
gdf_ic = gpd.read_file(ic_shp, encoding="euc-kr")
cheongna = gdf_ic[gdf_ic["remark"] == "국제업무단지"].copy()
cheongna_wgs = cheongna.to_crs(epsg=4326)
cheongna_wgs.to_file(OUT / "cheongna_boundary.geojson", driver="GeoJSON")

area_cheongna = float(cheongna["dgm_ar"].iloc[0])
print(f"  → 청라 면적: {area_cheongna:,.0f} m²  ({area_cheongna/1_000_000:.2f} km²)")
print(f"  → 저장: {OUT / 'cheongna_boundary.geojson'}")

print("\n완료!")
print(f"판교 / 청라 면적 비율: {area_pangyo/area_cheongna:.2f}x")
