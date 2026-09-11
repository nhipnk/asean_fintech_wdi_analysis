import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

import data_analysis as da  
import noi_dung_phan_tich as np_ 

ASEAN_COUNTRIES = da.ASEAN_COUNTRIES     
VN_NAMES = da.VN_COUNTRY_NAMES          
COLORS = da.COLORS
INDICATORS = da.INDICATORS

PAPER = "#EEF2EE"
INK = "#0F2027"
JADE = "#146B5F"
GOLD = "#B8862E"


@st.cache_data(ttl=60 * 60 * 12, show_spinner=False)
def get_data():
    """Bọc data_analysis.get_all_data() bằng cache của Streamlit."""
    return da.get_all_data(use_cache=True)


def iso_of(country_name: str) -> str:
    for iso, name in ASEAN_COUNTRIES.items():
        if name == country_name:
            return iso
    return None


# --------------------------------------------------------------------------
# GIAO DIỆN STREAMLIT
# --------------------------------------------------------------------------

st.set_page_config(
    page_title="Tài chính số & Bất bình đẳng — ASEAN",
    page_icon="📊",
    layout="wide",
)

st.markdown(f"""
<style>
    .stApp {{ background-color: {PAPER}; }}
    .hero {{
        background:{INK}; color:{PAPER}; padding:40px 32px; border-radius:4px; margin-bottom:24px;
    }}
    .hero .kicker {{ color:{GOLD}; font-size:0.85rem; border-left:2px solid {GOLD}; padding-left:10px; }}
    .hero h1 {{ font-weight:600; line-height:1.2; }}
    .chapter-label {{ color:{JADE}; font-weight:600; font-size:0.85rem; text-transform:uppercase; }}
    div[data-testid="stMetricValue"] {{ color:{JADE}; }}
    .story-box {{
        background:#FFFFFF; border-left:3px solid {JADE}; border-radius:4px;
        padding:16px 20px; margin:16px 0; color:{INK}; font-size:0.98rem; line-height:1.55;
    }}
</style>
""", unsafe_allow_html=True)


def story(markdown_text: str):
    """Hiển thị 1 đoạn phân tích TĨNH (viết trong noi_dung_phan_tich.py) — không ai sửa được trên web."""
    st.markdown(f'<div class="story-box">{markdown_text}</div>', unsafe_allow_html=True)

with st.spinner("Đang tải / đọc dữ liệu World Bank API…"):
    df_long, df_clean, df_wide = get_data()

# ---------------- HERO ----------------
st.markdown(f"""
<div class="hero">
  <p class="kicker">Đồ án dữ liệu · World Development Indicators, World Bank</p>
  <h1>Tài chính số có thu hẹp khoảng cách giàu nghèo ở ASEAN,<br>hay đang mở ra một khoảng cách mới?</h1>
  <p style="max-width:62ch;color:#C7D6D2;font-size:1.05rem;">
  Từ 2004 đến 2023, Internet và ví điện tử đã đi vào từng ngóc ngách của Đông Nam Á.
  Trang này ghép 5 chỉ tiêu WDI của 10 nước ASEAN để đọc lại câu chuyện đó — và để bạn viết
  phần phân tích của riêng mình ngay bên cạnh từng biểu đồ.</p>
</div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
c1.metric("Quốc gia ASEAN", "10")
c2.metric("Chỉ tiêu WDI", "5")
c3.metric("Giai đoạn theo dõi", "2004–2023")

st.divider()

# ---------------- CHƯƠNG 1: Internet ----------------
st.markdown('<p class="chapter-label">Chương 1</p>', unsafe_allow_html=True)
st.header("Đông Nam Á lên mạng")

story(np_.CH1_MO_DAU)

st.subheader("Tỷ lệ dân số sử dụng Internet (%)")
st.caption("World Bank WDI · `IT.NET.USER.ZS` · 2004–2023")

fig_net = go.Figure()
for iso, en_name in ASEAN_COUNTRIES.items():
    sub = df_wide[df_wide.country == en_name].dropna(subset=["IT.NET.USER.ZS"]).sort_values("year")
    fig_net.add_trace(go.Scatter(
        x=sub.year, y=sub["IT.NET.USER.ZS"], mode="lines", name=VN_NAMES[iso],
        line=dict(color=COLORS[iso], width=2),
    ))
fig_net.update_layout(
    plot_bgcolor="white", paper_bgcolor="white", height=460,
    yaxis_title="% dân số", xaxis_title="Năm",
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    margin=dict(t=10, l=10, r=10, b=10),
)
st.plotly_chart(fig_net, use_container_width=True)

story(np_.CH1_NHAN_XET)

st.divider()

# ---------------- CHƯƠNG 2: Findex + Bank branches ----------------
st.markdown('<p class="chapter-label">Chương 2</p>', unsafe_allow_html=True)
st.header("Từ có mạng đến có tài khoản")

story(np_.CH2_MO_DAU)

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Sở hữu tài khoản tài chính (% dân số 15+, năm gần nhất)")
    st.caption("WDI (Global Findex) · `FX.OWN.TOTL.ZS`")
    findex_rows = []
    for iso, en_name in ASEAN_COUNTRIES.items():
        sub = df_wide[df_wide.country == en_name].dropna(subset=["FX.OWN.TOTL.ZS"]).sort_values("year")
        if not sub.empty:
            last = sub.iloc[-1]
            findex_rows.append({"country": VN_NAMES[iso], "iso": iso,
                                 "value": last["FX.OWN.TOTL.ZS"], "year": int(last.year)})
    findex_df = pd.DataFrame(findex_rows).sort_values("value")
    if not findex_df.empty:
        fig_findex = px.bar(
            findex_df, x="value", y="country", orientation="h",
            color="iso", color_discrete_map=COLORS, text="value",
        )
        fig_findex.update_traces(texttemplate="%{text:.1f}%", showlegend=False)
        fig_findex.update_layout(
            plot_bgcolor="white", paper_bgcolor="white", height=420,
            xaxis_title="% dân số 15+", yaxis_title="", margin=dict(t=10, l=10, r=10, b=10),
        )
        st.plotly_chart(fig_findex, use_container_width=True)
    else:
        st.warning("Chưa có dữ liệu Findex khớp.")

with col_b:
    st.subheader("Chi nhánh ngân hàng (trên 100.000 người lớn, năm gần nhất)")
    st.caption("WDI · `FB.CBK.BRCH.P5`")
    branch_latest = da.branch_latest_by_country(df_clean)
    branch_latest = branch_latest.copy()
    branch_latest["iso"] = branch_latest["country"].map(iso_of)
    branch_latest["country_vn"] = branch_latest["iso"].map(VN_NAMES)
    fig_branch = px.bar(
        branch_latest.sort_values("value"), x="value", y="country_vn", orientation="h",
        color="iso", color_discrete_map=COLORS, text="value",
    )
    fig_branch.update_traces(texttemplate="%{text:.1f}", showlegend=False)
    fig_branch.update_layout(
        plot_bgcolor="white", paper_bgcolor="white", height=420,
        xaxis_title="Số chi nhánh / 100k người lớn", yaxis_title="",
        margin=dict(t=10, l=10, r=10, b=10),
    )
    st.plotly_chart(fig_branch, use_container_width=True)

story(np_.CH2_SO_SANH)

st.divider()

# ---------------- CHƯƠNG 3: Số hóa & bất bình đẳng ----------------
st.markdown('<p class="chapter-label">Chương 3</p>', unsafe_allow_html=True)
st.header("Số hóa và bất bình đẳng: cùng chiều hay ngược chiều?")

st.subheader("Internet penetration (%) so với chỉ số Gini")
st.caption("Mỗi điểm là một cặp quốc gia–năm · `IT.NET.USER.ZS` vs `SI.POV.GINI`")

scatter_df = da.internet_vs_gini(df_wide).copy()
scatter_df["iso"] = scatter_df["country"].map(iso_of)
scatter_df["country_vn"] = scatter_df["iso"].map(VN_NAMES)

fig_scatter = px.scatter(
    scatter_df, x="IT.NET.USER.ZS", y="SI.POV.GINI", color="iso", color_discrete_map=COLORS,
    hover_data=["country_vn", "year"],
)
fig_scatter.update_layout(
    plot_bgcolor="white", paper_bgcolor="white", height=460,
    xaxis_title="Internet users (%)", yaxis_title="Gini index",
    margin=dict(t=10, l=10, r=10, b=10),
)
st.plotly_chart(fig_scatter, use_container_width=True)

if len(scatter_df) > 2:
    corr = scatter_df["IT.NET.USER.ZS"].corr(scatter_df["SI.POV.GINI"])
    st.info(f"Hệ số tương quan Pearson giữa Internet penetration và Gini: **r = {corr:.3f}** "
            f"(n = {len(scatter_df)} cặp quốc gia–năm).")
else:
    st.warning("Không đủ dữ liệu trùng khớp để tính tương quan.")

story(np_.CH3_DOC_TUONG_QUAN)

st.subheader("Việt Nam: tăng trưởng GDP đầu người và chỉ số Gini")
st.caption("`NY.GDP.PCAP.KD.ZG` (trục trái) và `SI.POV.GINI` (trục phải)")

vn = df_wide[df_wide.country_iso3 == "VNM"].sort_values("year")
vn_gdp = vn.dropna(subset=["NY.GDP.PCAP.KD.ZG"])
vn_gini = vn.dropna(subset=["SI.POV.GINI"])

fig_vn = go.Figure()
fig_vn.add_trace(go.Scatter(x=vn_gdp.year, y=vn_gdp["NY.GDP.PCAP.KD.ZG"], name="GDP/đầu người, tăng trưởng %",
                             line=dict(color=JADE, width=2), yaxis="y1"))
fig_vn.add_trace(go.Scatter(x=vn_gini.year, y=vn_gini["SI.POV.GINI"], name="Gini index",
                             line=dict(color=GOLD, width=2, dash="dot"), yaxis="y2"))
fig_vn.update_layout(
    plot_bgcolor="white", paper_bgcolor="white", height=440,
    xaxis_title="Năm",
    yaxis=dict(title="Tăng trưởng GDP/đầu người (%)"),
    yaxis2=dict(title="Gini index", overlaying="y", side="right"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    margin=dict(t=10, l=10, r=10, b=10),
)
st.plotly_chart(fig_vn, use_container_width=True)

st.subheader("Ma trận tương quan giữa 5 chỉ tiêu (toàn mẫu ASEAN)")
st.caption("Hệ số Pearson, tính trên các cặp quốc gia–năm có đủ dữ liệu")

corr_matrix = da.correlation_matrix(df_wide)
labels = [INDICATORS[c] for c in corr_matrix.columns]
fig_heat = px.imshow(
    corr_matrix.values, x=labels, y=labels, color_continuous_scale="RdYlGn",
    zmin=-1, zmax=1, text_auto=".2f", aspect="auto",
)
fig_heat.update_layout(height=460, margin=dict(t=10, l=10, r=10, b=10))
st.plotly_chart(fig_heat, use_container_width=True)

st.subheader("So sánh nhanh Internet penetration giữa 10 nước")
st.caption("Biểu đồ nhỏ (sparkline), cùng thang thời gian 2004–2023")

spark_cols = st.columns(5)
for idx, (iso, en_name) in enumerate(ASEAN_COUNTRIES.items()):
    sub = df_wide[df_wide.country == en_name].dropna(subset=["IT.NET.USER.ZS"]).sort_values("year")
    fig_spark = go.Figure(go.Scatter(x=sub.year, y=sub["IT.NET.USER.ZS"], mode="lines",
                                      line=dict(color=COLORS[iso], width=2), fill="tozeroy"))
    fig_spark.update_layout(
        height=120, margin=dict(t=24, l=0, r=0, b=0),
        title=dict(text=VN_NAMES[iso], font=dict(size=12)),
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        plot_bgcolor="white", paper_bgcolor="white", showlegend=False,
    )
    with spark_cols[idx % 5]:
        st.plotly_chart(fig_spark, use_container_width=True)

story(np_.CH3_KET_CHUONG)

st.divider()

# ---------------- KIỂM TRA CHÉO ----------------
st.markdown('<p class="chapter-label">Kiểm tra chéo dữ liệu</p>', unsafe_allow_html=True)
st.header("Đối chiếu với một nguồn độc lập")

st.write(
    "Tỷ lệ dùng Internet của Việt Nam năm 2022 theo World Bank WDI, đối chiếu với báo cáo "
    "*Digital 2022: Vietnam* của DataReportal (We Are Social & Kepios, tháng 1/2022)."
)

cross_check = da.cross_check_vietnam_internet(df_wide).iloc[0]
cc1, cc2, cc3 = st.columns(3)
cc1.metric(f"World Bank WDI, {cross_check.matched_year}", f"{cross_check.gia_tri_nguon_1:.1f}%")
cc2.metric("DataReportal, 1/2022", f"{cross_check.gia_tri_nguon_2}%")
cc3.metric("Chênh lệch (điểm %)", f"{cross_check['chenh_lech_diem_%']:+.1f}")

st.caption(
    "Chênh lệch có thể đến từ thời điểm đo khác nhau trong năm và phương pháp khác nhau "
    "(khảo sát hộ gia đình/ITU so với ước tính từ dữ liệu nhà mạng). "
    "Nguồn: https://datareportal.com/reports/digital-2022-vietnam"
)

st.divider()

# ---------------- PHƯƠNG PHÁP & DỮ LIỆU ----------------
st.markdown('<p class="chapter-label">Phương pháp & dữ liệu</p>', unsafe_allow_html=True)
st.header("Danh sách chỉ tiêu WDI")

st.table(da.build_metadata_table())

with st.expander("📊 Độ phủ dữ liệu theo nước / chỉ tiêu"):
    coverage = da.data_coverage(df_clean)
    st.dataframe(coverage.pivot(index="country", columns="indicator_code", values="so_nam_co_du_lieu"))

with st.expander("📊 Thống kê mô tả tổng quan (toàn ASEAN, 2004–2023)"):
    st.dataframe(da.descriptive_stats(df_clean))

st.write(
    "Dữ liệu trên trang này lấy từ World Bank API (`api.worldbank.org/v2`), dùng chung logic "
    "tải/làm sạch với notebook `asean_fintech_wdi_analysis.ipynb` (file `data_analysis.py`). "
    "Nếu đã có `data/raw_wdi_long.csv` (chạy từ notebook trước đó), app sẽ đọc lại từ cache đó "
    "thay vì gọi API mỗi lần mở trang."
)

story(np_.KHAI_BAO_AI)

st.divider()

# ---------------- NGUỒN & TÀI LIỆU THAM KHẢO ----------------
st.header("Nguồn & tài liệu tham khảo")
st.markdown(
    "- World Bank. *World Development Indicators.* https://data.worldbank.org/\n"
    "- DataReportal. *Digital 2022: Vietnam.* We Are Social & Kepios, 2022. "
    "https://datareportal.com/reports/digital-2022-vietnam"
)
story(np_.TAI_LIEU_THAM_KHAO_BO_SUNG)

st.caption(
    "Trang dữ liệu này lấy số liệu qua World Bank API (hoặc cache CSV từ notebook). Nếu biểu đồ "
    "không hiện, hãy kiểm tra kết nối Internet hoặc file cache — không phải do file bị hỏng."
)
