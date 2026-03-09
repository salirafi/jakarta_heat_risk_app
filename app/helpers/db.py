import sqlite3
import geopandas as gpd
import pandas as pd
from shapely import wkt

from config import DB_PATH, BOUNDARY_TABLE, FORECAST_TABLE

def run_query(query: str) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    try:
        return pd.read_sql_query(query, conn)
    finally:
        conn.close()

def get_table_names() -> list[str]:
    tables = run_query("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    return tables["name"].tolist()

def load_boundary_data() -> gpd.GeoDataFrame:
    query = f"SELECT * FROM {BOUNDARY_TABLE}"
    boundary_df = run_query(query)

    if boundary_df.empty:
        return gpd.GeoDataFrame(boundary_df, geometry=[], crs="EPSG:4326")

    boundary_df["adm4"] = boundary_df["adm4"].astype(str).str.strip()
    boundary_df["geometry"] = boundary_df["geometry_wkt"].apply(wkt.loads)

    gdf = gpd.GeoDataFrame(boundary_df, geometry="geometry", crs="EPSG:4326")

    # Drop missing geometries
    gdf = gdf[gdf.geometry.notna()].copy()

    # Try repairing invalid geometries
    invalid_mask = ~gdf.geometry.is_valid
    if invalid_mask.any():
        gdf.loc[invalid_mask, "geometry"] = gdf.loc[invalid_mask, "geometry"].buffer(0)

    # Drop anything still invalid or empty after repair
    gdf = gdf[gdf.geometry.notna()].copy()
    gdf = gdf[~gdf.geometry.is_empty].copy()
    gdf = gdf[gdf.geometry.is_valid].copy()

    # Keep one row per polygon id
    gdf = gdf.drop_duplicates(subset=["adm4"]).reset_index(drop=True)

    return gdf

def load_forecast_data() -> pd.DataFrame:
    query = f"""
    SELECT
        adm4,
        desa_kelurahan,
        kecamatan,
        kotkab,
        local_datetime,
        temperature_c,
        humidity_pct,
        heat_index_c,
        risk_level,
        weather_desc_en
    FROM {FORECAST_TABLE}
    ORDER BY local_datetime
    """
    df = run_query(query)

    if df.empty:
        return df

    df["local_datetime"] = pd.to_datetime(df["local_datetime"], errors="coerce")

    for col in ["adm4", "desa_kelurahan", "kecamatan", "kotkab", "risk_level", "weather_desc_en"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    df = df.dropna(subset=["local_datetime"]).reset_index(drop=True)
    return df