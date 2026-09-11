# -*- coding: utf-8 -*-
"""
data_analysis.py
-----------------
Bản module hóa (import được) của notebook `asean_fintech_wdi_analysis.ipynb`.
Toàn bộ tên hàm, tên cột, logic xử lý được giữ NGUYÊN như trong notebook, để
`app.py` (Streamlit UI) và notebook luôn cho ra cùng một kết quả khi cùng chạy.

Có thể chạy độc lập: `python data_analysis.py` để tái tạo các file CSV trong
`data/` giống hệt khi chạy notebook.
"""

import os
import time
import json
import requests
import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# Bước 1 — Cấu hình: Quốc gia → Mã chỉ tiêu → Khoảng thời gian
# --------------------------------------------------------------------------

ASEAN_COUNTRIES = {
    "VNM": "Vietnam",
    "IDN": "Indonesia",
    "MYS": "Malaysia",
    "PHL": "Philippines",
    "THA": "Thailand",
    "SGP": "Singapore",
    "KHM": "Cambodia",
    "LAO": "Lao PDR",
    "MMR": "Myanmar",
    "BRN": "Brunei Darussalam",
}

# Tên tiếng Việt để hiển thị trên UI (notebook dùng tên tiếng Anh của World Bank)
VN_COUNTRY_NAMES = {
    "VNM": "Việt Nam", "IDN": "Indonesia", "MYS": "Malaysia", "PHL": "Philippines",
    "THA": "Thái Lan", "SGP": "Singapore", "KHM": "Campuchia", "LAO": "Lào",
    "MMR": "Myanmar", "BRN": "Brunei",
}

COLORS = {
    "VNM": "#146B5F", "IDN": "#B8862E", "MYS": "#A6483A", "PHL": "#3B6E8C",
    "THA": "#6B8F3E", "SGP": "#0F2027", "KHM": "#C98A4B", "LAO": "#5C8A82",
    "MMR": "#8C6BAE", "BRN": "#4B7BA6",
}

INDICATORS = {
    "FX.OWN.TOTL.ZS": "Account ownership at a financial institution or mobile-money-service provider, % age 15+",
    "IT.NET.USER.ZS": "Individuals using the Internet, % of population",
    "SI.POV.GINI": "Gini index",
    "FB.CBK.BRCH.P5": "Commercial bank branches (per 100,000 adults)",
    "NY.GDP.PCAP.KD.ZG": "GDP per capita growth (annual %)",
}

DATE_RANGE = "2004:2023"   # 20 năm -> thỏa yêu cầu >= 10 năm

RAW_CACHE_PATH = "data/raw_wdi_long.csv"
USE_CACHE_IF_AVAILABLE = True
WB_BASE_URL = "https://api.worldbank.org/v2/country/{countries}/indicator/{indicator}"

DATAREPORTAL_VN_2022 = 73.2  # % Internet users, Digital 2022: Vietnam (We Are Social & Kepios)


# --------------------------------------------------------------------------
# Bước 2 — Gửi yêu cầu API và nhận dữ liệu (giống hệt notebook)
# --------------------------------------------------------------------------

def fetch_indicator(indicator_code, countries=ASEAN_COUNTRIES, date_range=DATE_RANGE,
                     per_page=1000, max_retries=3, sleep_between=0.5):
    """Gọi World Bank API cho 1 chỉ tiêu, trả về list các bản ghi thô (đã gộp mọi trang)."""
    country_str = ";".join(countries.keys())
    url = WB_BASE_URL.format(countries=country_str, indicator=indicator_code)
    all_records = []
    page = 1

    while True:
        params = {"format": "json", "date": date_range, "per_page": per_page, "page": page}
        last_err = None
        payload = None
        for attempt in range(1, max_retries + 1):
            try:
                resp = requests.get(url, params=params, timeout=30)
                resp.raise_for_status()
                payload = resp.json()
                break
            except (requests.RequestException, json.JSONDecodeError) as e:
                last_err = e
                time.sleep(1.5 * attempt)
        if payload is None:
            raise RuntimeError(f"Không gọi được API cho {indicator_code} (trang {page}): {last_err}")

        if not isinstance(payload, list) or len(payload) < 2 or payload[1] is None:
            break

        meta, records = payload[0], payload[1]
        all_records.extend(records)

        total_pages = meta.get("pages", 1) or 1
        if page >= total_pages:
            break
        page += 1
        time.sleep(sleep_between)

    return all_records


def records_to_dataframe(records, indicator_code, indicator_name):
    """Chuyển 1 list bản ghi JSON của World Bank thành DataFrame gọn (long format)."""
    rows = []
    for r in records:
        rows.append({
            "country_iso3": r.get("countryiso3code"),
            "country": (r.get("country") or {}).get("value"),
            "indicator_code": indicator_code,
            "indicator_name": indicator_name,
            "year": int(r["date"]) if r.get("date") else None,
            "value": r.get("value"),
        })
    return pd.DataFrame(rows)


def fetch_all_indicators(indicators=INDICATORS, countries=ASEAN_COUNTRIES, date_range=DATE_RANGE):
    """Gọi API cho toàn bộ chỉ tiêu, gộp thành 1 bảng dài (long/tidy format)."""
    frames = []
    for code_, name in indicators.items():
        records = fetch_indicator(code_, countries=countries, date_range=date_range)
        df_i = records_to_dataframe(records, code_, name)
        frames.append(df_i)
    df_long = pd.concat(frames, ignore_index=True)
    df_long = df_long.dropna(subset=["country_iso3"])
    return df_long


# --------------------------------------------------------------------------
# Bước 3 — Tải dữ liệu (có cache CSV, giống notebook)
# --------------------------------------------------------------------------

def load_data(use_cache=USE_CACHE_IF_AVAILABLE, cache_path=RAW_CACHE_PATH):
    """Đọc từ cache CSV nếu có, ngược lại gọi API và lưu cache lại."""
    if use_cache and os.path.exists(cache_path):
        return pd.read_csv(cache_path)
    os.makedirs(os.path.dirname(cache_path) or ".", exist_ok=True)
    df_long = fetch_all_indicators()
    df_long.to_csv(cache_path, index=False)
    return df_long


# --------------------------------------------------------------------------
# Bước 4 — Làm sạch & chuyển sang bảng rộng (wide format), giống notebook
# --------------------------------------------------------------------------

def clean_and_widen(df_long: pd.DataFrame):
    """Trả về (df_clean, df_wide) — đúng logic Bước 4 trong notebook."""
    df_clean = df_long.dropna(subset=["value"]).copy()
    df_clean["value"] = pd.to_numeric(df_clean["value"], errors="coerce")

    df_wide = (
        df_clean
        .pivot_table(index=["country", "country_iso3", "year"],
                     columns="indicator_code", values="value")
        .reset_index()
        .sort_values(["country", "year"])
    )
    return df_clean, df_wide


# --------------------------------------------------------------------------
# Bước 5 — Bảng mô tả dữ liệu, độ phủ dữ liệu, thống kê mô tả
# --------------------------------------------------------------------------

def build_metadata_table():
    return pd.DataFrame({
        "indicator_code": list(INDICATORS.keys()),
        "indicator_name": list(INDICATORS.values()),
        "source": ["World Bank – World Development Indicators (WDI)"] * len(INDICATORS),
        "unit": ["% dân số 15+", "% dân số", "chỉ số 0-100",
                 "chi nhánh / 100,000 người lớn", "% / năm"],
    })


def data_coverage(df_clean: pd.DataFrame) -> pd.DataFrame:
    return (
        df_clean.groupby(["country", "indicator_code"])["year"]
        .agg(so_nam_co_du_lieu="count", nam_dau="min", nam_cuoi="max")
        .reset_index()
    )


def descriptive_stats(df_clean: pd.DataFrame) -> pd.DataFrame:
    return df_clean.groupby("indicator_code")["value"].describe()[["count", "mean", "std", "min", "max"]]


# --------------------------------------------------------------------------
# Bước 6 — Kiểm tra chéo với DataReportal (giống hệt logic notebook)
# --------------------------------------------------------------------------

def cross_check_vietnam_internet(df_wide: pd.DataFrame,
                                  external_value_jan2022: float = DATAREPORTAL_VN_2022) -> pd.DataFrame:
    mask = (
        df_wide["country"].isin(["Vietnam", "Viet Nam"]) &
        (df_wide["year"].astype(str) == "2022")
    )
    matched_series = df_wide.loc[mask, "IT.NET.USER.ZS"].dropna()

    if not matched_series.empty:
        wb_value_2022 = matched_series.values[0]
        matched_year = "2022"
    else:
        fallback_row = df_wide[
            (df_wide["country"].isin(["Vietnam", "Viet Nam"])) &
            (df_wide["IT.NET.USER.ZS"].notna())
        ].sort_values("year").iloc[-1]
        wb_value_2022 = fallback_row["IT.NET.USER.ZS"]
        matched_year = str(fallback_row["year"])

    external_source = "DataReportal – Digital 2022: Vietnam (We Are Social & Kepios, T1/2022)"
    diff = wb_value_2022 - external_value_jan2022

    return pd.DataFrame([{
        "indicator": "IT.NET.USER.ZS (% dùng Internet, Việt Nam)",
        "nguon_1": f"World Bank WDI (API, {matched_year})",
        "gia_tri_nguon_1": round(float(wb_value_2022), 2),
        "nguon_2": external_source,
        "gia_tri_nguon_2": external_value_jan2022,
        "chenh_lech_diem_%": round(float(diff), 2),
        "matched_year": matched_year,
    }])


# --------------------------------------------------------------------------
# Bước 7 — Các phép tính dùng cho trực quan hóa
# --------------------------------------------------------------------------

def internet_vs_gini(df_wide: pd.DataFrame) -> pd.DataFrame:
    """Bảng scatter Internet% vs Gini — đúng logic Hình 3 trong notebook."""
    return df_wide.dropna(subset=["IT.NET.USER.ZS", "SI.POV.GINI"])


def correlation_matrix(df_wide: pd.DataFrame) -> pd.DataFrame:
    """Ma trận tương quan 5 chỉ tiêu — đúng logic Hình 6 trong notebook."""
    return df_wide[list(INDICATORS.keys())].corr()


def branch_latest_by_country(df_clean: pd.DataFrame) -> pd.DataFrame:
    """Chi nhánh ngân hàng, năm gần nhất mỗi nước — đúng logic Hình 4 trong notebook."""
    return (
        df_clean[df_clean["indicator_code"] == "FB.CBK.BRCH.P5"]
        .sort_values("year")
        .groupby("country")
        .tail(1)
        .sort_values("value", ascending=False)
    )


def get_all_data(use_cache=USE_CACHE_IF_AVAILABLE):
    """Tiện ích: tải + làm sạch trong 1 lần gọi, trả về (df_long, df_clean, df_wide)."""
    df_long = load_data(use_cache=use_cache)
    df_clean, df_wide = clean_and_widen(df_long)
    return df_long, df_clean, df_wide


if __name__ == "__main__":
    df_long, df_clean, df_wide = get_all_data()
    print(f"df_long: {df_long.shape}, df_wide: {df_wide.shape}")
    print("\nMa trận tương quan:")
    print(correlation_matrix(df_wide).round(2))
    print("\nKiểm tra chéo Việt Nam - Internet 2022:")
    print(cross_check_vietnam_internet(df_wide))