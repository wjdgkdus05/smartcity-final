# 데이터로 진단하는 업무지구의 성공과 실패
**판교테크노밸리 vs 청라국제업무·금융단지 비교분석**

> 스마트시티 이론과 실제 기말 프로젝트  
> 배포 사이트: https://wjdgkdus05.github.io/smartcity-final

---

## 프로젝트 개요

성공 사례로 많이 언급되는 **판교테크노밸리**와 조성은 완료되었으나 장기 미활성화 상태인 **청라국제업무·금융단지**를 대상으로, 공공데이터 기반 비교분석 시스템을 구축하고 업무지구 성공요인을 데이터 근거와 함께 도출하고자 함 

---

## 분석 구역계

| 구분 | 판교테크노밸리 | 청라국제업무·금융단지 |
|---|---|---|
| 면적 | 597,304㎡ | 884,942㎡ |
| 핵심역 | 판교역 (신분당선) | 청라국제도시역 (공항철도) |
| 구역계 출처 | 공식 배치도 기반 직접 디지타이징 | 청라개발계획안내도(2025) 기반 직접 디지타이징 |

---

## 데이터 출처

| 데이터 | 출처 | 기준 |
|---|---|---|
| 집계구 경계 SHP | SGIS 통계지리정보서비스 | 2025년 2분기 |
| 집계구 인구 | SGIS 통계지리정보서비스 | 2024년 |
| 집계구 종사자·사업체 | SGIS 전국사업체조사 | 2023년 |
| 용도지역 SHP | VWorld 토지이용계획공간정보 | 2026-04-12 기준 |
| 건축물대장 | 건축데이터 민간개방시스템 (건축HUB) | 2026년 4월 기준 |
| 연속지적도 | 국가공간정보포털 (nsdi.go.kr) | 2026년 5월 기준 |
| 지하철 네트워크 | 수업 제공 subway_network.zip | 2026-06-15 기준 |
| 도로망 | OpenStreetMap (osmnx) | 2026년 6월 수집 |
| 베이스맵 | VWorld WMTS, OpenStreetMap, CartoDB | - |

---

## 분석 지표

### 토지이용
- 용도지역 구성비 (VWorld 용도지역 SHP)
- 건축물 주용도 구성비 (건축물대장 + 연속지적도 PNU 조인)
- 토지이용 혼합도 (LUM 엔트로피)
- 개발 실현 정도 (평균 용적률, 미건축 필지 비율)

### 교통망
- 30분·60분 등시간권 (다익스트라, subway_network.zip)
- 등시간권 내 도달 인구·종사자 (등시간권 × SGIS 집계구 공간결합)
- 누적 접근성 곡선 (5분 단위)
- 역세권 면적 비율 (핵심역 1km 버퍼)
- 도로망 밀도 (OSM, osmnx)

### 인구사회
- 구역 내 인구·종사자·사업체 (집계구 centroid 기준 선택 후 클리핑)
- 직주비 (종사자수 / 상주인구)
- 업종(산업분류 10차 대분류) 구성

---

## 데이터 처리 과정

```
data/raw/              ← 원본 데이터 (git 추적 제외)
data/processed/        ← 전처리 결과
web/data/              ← 웹사이트용 경량화 GeoJSON
scripts/               ← 전처리 스크립트
```

### 주요 스크립트

| 스크립트 | 설명 |
|---|---|
| `scripts/process_sgis.py` | 집계구 경계 + 인구·종사자 통합 |
| `scripts/process_landuse.py` | 용도지역 SHP 클리핑 |
| `scripts/analyze_landuse.py` | 용도지역 구성비·LUM 산출 |
| `scripts/analyze_buildings_cheongna.py` | 건축물 용도 분류 (오피스텔 분리) |
| `scripts/isochrone_analysis.py` | 다익스트라 등시간권 분석 |
| `scripts/make_isochrone.py` | 등시간권 폴리곤 생성 (역 3km 버퍼 합집합) |
| `scripts/make_path_tree.py` | 최단경로 트리 시각화용 선 생성 |
| `scripts/analyze_auxiliary.py` | 역세권 면적비율·도로망 밀도 |
| `scripts/analyze_industry.py` | 업종(산업분류) 구성 분석 |
| `scripts/fix_oa.py` | 집계구 구역계 클리핑 |

### 공간단위 통합 처리

집계구 경계와 분석 구역계가 일치하지 않는 문제를 다음과 같이 처리하였음
집계구 centroid가 구역계 내부에 위치하는 집계구를 선택하고, 선택된 집계구를 구역계로 클리핑하여 경계부 오차를 제거

---

## AI 활용 내역

본 프로젝트는 Claude를 활용해 다음 작업을 수행함

- 데이터 전처리 스크립트 작성 (Python/GeoPandas)
- 다익스트라 등시간권 분석 코드 작성
- 웹사이트 (HTML/CSS/JavaScript/Leaflet.js) 코드 작성

구역계 정의·데이터 수집·분석 결과 검증·보고서 최종 서술은 본인이 직접 수행하였으며, AI 생성 코드의 정확성 검증 책임은 본인에게 있음

---

## 시스템 구조

```
index.html
data/
  pangyo_tv1_final.geojson
  cheongna_final2.geojson
  landuse_pangyo.geojson
  landuse_cheongna2.geojson
  bld_pangyo.geojson
  bld_cheongna.geojson
  isochrone_pangyo_30min.geojson
  isochrone_pangyo_60min.geojson
  isochrone_cheongna_30min.geojson
  isochrone_cheongna_60min.geojson
  path_tree_pangyo_30min.geojson
  path_tree_pangyo_60min.geojson
  path_tree_cheongna_30min.geojson
  path_tree_cheongna_60min.geojson
  oa_pangyo_inner.geojson
  oa_cheongna_inner.geojson
```
