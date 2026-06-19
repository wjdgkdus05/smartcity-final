import geopandas as gpd
import pandas as pd

bld_pg = gpd.read_file(r"C:\smartcity_final_exam\web\data\bld_pangyo.geojson")
bld_pg['용적률(%)'] = pd.to_numeric(bld_pg.get('용적률(%)'), errors='coerce')
far = bld_pg[bld_pg['용적률(%)'] > 0]['용적률(%)'].mean()
print(f"평균 용적률: {far:.1f}%")