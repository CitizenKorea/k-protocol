import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import gzip
import io
import requests
from scipy.stats import pearsonr
from fpdf import FPDF
import datetime

# ==========================================
# 1. K-PROTOCOL Universal Constants (절대 상수)
# ==========================================
G_SI = 9.80665
S_EARTH = (np.pi**2) / G_SI 
C_SI = 299792458
C_K = C_SI / S_EARTH
R_EARTH = 6371000

# ==========================================
# 2. Page Configuration & CSS Styling (밝은 테마)
# ==========================================
st.set_page_config(page_title="K-PROTOCOL Analysis Center", layout="wide", page_icon="🛰️")

st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; color: #212529; }
    .metric-box { background-color: #FFFFFF; padding: 20px; border-left: 4px solid #0056B3; border-radius: 5px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .metric-title { font-size: 14px; color: #6C757D; text-transform: uppercase; letter-spacing: 1px; font-weight: bold; }
    .metric-value { font-size: 28px; font-weight: 700; color: #212529; }
    .philosophical-quote { background-color: #FFFFFF; border: 1px solid #DEE2E6; border-radius: 8px; padding: 25px; font-style: normal; color: #495057; text-align: center; margin-top: 30px; margin-bottom: 30px; }
    .link-box a { color: #0056B3; text-decoration: none; font-weight: bold; }
    hr { border-color: #DEE2E6; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. 깃허브 실시간 데이터 연동 (조작 없는 실제 수치)
# ==========================================
@st.cache_data(ttl=600)
def get_github_stats():
    repo_url = "https://api.github.com/repos/CitizenKorea/k-protocol"
    try:
        response = requests.get(repo_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("stargazers_count", 0), data.get("forks_count", 0)
        return 0, 0
    except:
        return 0, 0

real_stars, real_forks = get_github_stats()

# ==========================================
# 4. Dictionary (KOR / ENG)
# ==========================================
if 'lang' not in st.session_state:
    st.session_state['lang'] = 'ENG'
lang = st.session_state['lang']

i18n = {
    'KOR': {
        'title': "K-PROTOCOL 오픈 분석 센터",
        'subtitle': "데이터로 증명하고, 스스로 판단하십시오.",
        'upload_prompt': "SNX, SP3, CLK 파일을 드래그 앤 드롭 하십시오",
        'insight_msg': "분석 결과는 업로드된 데이터를 기반으로 연산된 수학적 사실입니다. 이 수치가 물리적으로 무엇을 의미하는지는 방문자 스스로 고민해 보시길 권합니다.",
    },
    'ENG': {
        'title': "K-PROTOCOL Open Analysis Center",
        'subtitle': "Let the data speak. Judge for yourself.",
        'upload_prompt': "Drag and drop SNX, SP3, or CLK files",
        'insight_msg': "The analysis results are mathematical facts calculated directly from the uploaded data. We invite visitors to ponder the physical meaning behind these numbers.",
    }
}
t = i18n[lang]

# ==========================================
# 5. Header & Trust Metrics
# ==========================================
col_title, col_lang = st.columns([8, 1])
with col_title:
    st.markdown(f"<h1 style='color: #212529;'>{t['title']}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='color: #6C757D; font-weight: 300;'>{t['subtitle']}</h4>", unsafe_allow_html=True)
with col_lang:
    selected_lang = st.radio("Language", ["ENG", "KOR"], label_visibility="collapsed", horizontal=True)
    if selected_lang != st.session_state['lang']:
        st.session_state['lang'] = selected_lang
        st.rerun()

st.divider()

c1, c2, c3 = st.columns([1, 1, 2])
with c1:
    st.markdown(f'<div class="metric-box"><div class="metric-title">GITHUB STARS</div><div class="metric-value">{real_stars}</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-box"><div class="metric-title">GITHUB FORKS</div><div class="metric-value">{real_forks}</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown("**Data & References**")
    st.markdown("<div class='link-box'>📄 <a href='https://doi.org/10.5281/zenodo.18976813' target='_blank'>Theoretical Background (Zenodo)</a></div>", unsafe_allow_html=True)
    st.markdown("<div class='link-box'>📡 <a href='http://garner.ucsd.edu/pub/products/2392/' target='_blank'>Raw Data Directory (UCSD Garner)</a></div>", unsafe_allow_html=True)

st.divider()

# ==========================================
# 6. PDF Generation (100% 실측 데이터 기반)
# ==========================================
def create_integrity_report(df, file_type, r_sq=None, max_res=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(190, 10, "K-PROTOCOL Analytical Integrity Report", 0, 1, 'C')
    pdf.ln(5)
    
    pdf.set_font("helvetica", '', 10)
    pdf.cell(190, 8, f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1, 'L')
    pdf.cell(190, 8, f"Algorithm: K-PROTOCOL (Patent Pending)", 0, 1, 'L')
    pdf.cell(190, 8, f"Author: CK (CitizenKorea)", 0, 1, 'L')
    pdf.ln(10)
    
    # [SNX 3D 공간 데이터 인쇄 로직]
    if file_type == 'SNX' and not df.empty:
        pdf.set_font("helvetica", 'B', 12)
        pdf.cell(190, 10, "[ 3D Spatial Metric Calibration Results ]", 0, 1, 'L')
        pdf.set_font("helvetica", '', 10)
        
        if max_res is not None:
            pdf.cell(190, 8, f"Calculated Max Residual: {max_res:.6f} m", 0, 1, 'L')
        if r_sq is not None:
            pdf.cell(190, 8, f"Calculated Correlation (R-squared): {r_sq:.7f}%", 0, 1, 'L')
        
        pdf.ln(5)
        pdf.set_font("helvetica", 'B', 9)
        pdf.cell(40, 10, "Station ID", 1, 0, 'C')
        pdf.cell(40, 10, "Altitude (m)", 1, 0, 'C')
        pdf.cell(50, 10, "SI Distance (m)", 1, 0, 'C')
        pdf.cell(50, 10, "K-Residual (m)", 1, 1, 'C')
        
        pdf.set_font("helvetica", '', 8)
        for _, row in df.head(40).iterrows():
            pdf.cell(40, 8, str(row['ID'])[:15], 1, 0, 'C')
            pdf.cell(40, 8, f"{row['Altitude']:.2f}", 1, 0, 'C')
            pdf.cell(50, 8, f"{row['SI_Dist']:.2f}", 1, 0, 'C')
            pdf.cell(50, 8, f"{row['Residual']:.6f}", 1, 1, 'C')

    # [SP3/CLK 위성 시간 데이터 인쇄 로직]
    elif file_type == 'SP3' and not df.empty:
        pdf.set_font("helvetica", 'B', 12)
        pdf.cell(190, 10, "[ Absolute Time Synchronization Results ]", 0, 1, 'L')
        pdf.set_font("helvetica", '', 10)
        
        avg_residual = df['Temporal_Residual_us'].abs().mean()
        pdf.cell(190, 8, f"Analyzed Satellites: {len(df['Satellite_ID'].unique())}", 0, 1, 'L')
        pdf.cell(190, 8, f"Average Temporal Residual Extracted: {avg_residual:.6f} us", 0, 1, 'L')
        
        pdf.ln(5)
        pdf.set_font("helvetica", 'B', 9)
        pdf.cell(30, 10, "Satellite ID", 1, 0, 'C')
        pdf.cell(50, 10, "Raw Clock Bias (us)", 1, 0, 'C')
        pdf.cell(50, 10, "Calibrated Bias (us)", 1, 0, 'C')
        pdf.cell(50, 10, "Temporal Residual (us)", 1, 1, 'C')
        
        pdf.set_font("helvetica", '', 8)
        for _, row in df.head(40).iterrows():
            pdf.cell(30, 8, str(row['Satellite_ID'])[:15], 1, 0, 'C')
            pdf.cell(50, 8, f"{row['Clock_Bias_Raw_us']:.6f}", 1, 0, 'C')
            pdf.cell(50, 8, f"{row['Calibrated_Bias_us']:.6f}", 1, 0, 'C')
            pdf.cell(50, 8, f"{row['Temporal_Residual_us']:.6f}", 1, 1, 'C')

    pdf.ln(15)
    pdf.set_font("helvetica", 'I', 9)
    pdf.multi_cell(190, 6, "Notice: The calculation results are derived directly from the uploaded data files. We invite you to consider the physical essence of these metrics.")
    
    out = pdf.output(dest='S')
    return out.encode('latin-1') if isinstance(out, str) else bytes(out)

# ==========================================
# 7. Dynamic Analysis Engine (순수 연산 및 시각화)
# ==========================================
uploaded_file = st.file_uploader(t['upload_prompt'], type=["snx", "sp3", "clk", "gz"])

if uploaded_file:
    fname = uploaded_file.name.lower()
    df = pd.DataFrame()
    file_type_flag = None
    r_sq = None
    max_res = None
    
    with st.spinner("Processing actual data..."):
        # --- SNX Parser ---
        if ".snx" in fname:
            file_type_flag = 'SNX'
            snx_data = {}
            f = gzip.open(uploaded_file, 'rt') if fname.endswith('.gz') else io.TextIOWrapper(uploaded_file)
            capture = False
            for line in f:
                if line.startswith('+SOLUTION/ESTIMATE'): capture = True; continue
                if line.startswith('-SOLUTION/ESTIMATE'): capture = False; break
                if capture and any(a in line for a in ['STAX', 'STAY', 'STAZ']):
                    p = line.split()
                    if len(p) >= 9:
                        sid, axis, val = p[2], p[1], float(p[8])
                        if sid not in snx_data: snx_data[sid] = {}
                        snx_data[sid][axis] = val
            
            rows = []
            for sid, c in snx_data.items():
                if all(k in c for k in ['STAX', 'STAY', 'STAZ']):
                    R_SI = np.sqrt(c['STAX']**2 + c['STAY']**2 + c['STAZ']**2)
                    alt = R_SI - R_EARTH
                    g_loc = G_SI * ((R_EARTH / R_SI)**2)
                    s_loc = (np.pi**2) / g_loc
                    rows.append([sid, R_SI, alt, g_loc, s_loc])
            
            df = pd.DataFrame(rows, columns=['ID', 'SI_Dist', 'Altitude', 'g_loc', 'S_loc'])
            
            if not df.empty:
                df['K_Dist'] = df['SI_Dist'] / df['S_loc']
                df['Residual'] = df['SI_Dist'] - df['K_Dist']
                max_res = df['Residual'].abs().max()
                
                corr, _ = pearsonr(df['Altitude'], df['Residual'])
                r_sq = (corr**2) * 100
                
                st.subheader("Data Calculation Results (SNX)")
                fig = px.scatter(df, x='Altitude', y='Residual', hover_data=['ID'], 
                                 trendline="ols", trendline_color_override="#0056B3",
                                 title=f"Actual Correlation | R² = {r_sq:.7f}%",
                                 template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)
                
                format_dict_snx = {'Altitude': '{:.6f}', 'g_loc': '{:.6f}', 'S_loc': '{:.6f}', 'SI_Dist': '{:.6f}', 'K_Dist': '{:.6f}', 'Residual': '{:.6f}'}
                st.dataframe(df[['ID', 'Altitude', 'SI_Dist', 'K_Dist', 'Residual']].style.format(format_dict_snx), use_container_width=True)

        # --- SP3/CLK Parser (결측치 필터링 완벽 적용) ---
        elif any(x in fname for x in ['.sp3', '.clk']):
            file_type_flag = 'SP3'
            rows = []
            f = gzip.open(uploaded_file, 'rt') if fname.endswith('.gz') else io.TextIOWrapper(uploaded_file)
            for line in f:
                if "sp3" in fname and line.startswith('P'):
                    try: 
                        sat_id = line[1:4].strip()
                        clock_bias = float(line[46:60])
                        # 999999.999999 등 에러/결측치 데이터(Dummy Data) 원천 차단
                        if abs(clock_bias) < 900000.0:
                            rows.append([sat_id, clock_bias])
                    except: pass
                elif "clk" in fname and line.startswith('AS'):
                    p = line.split()
                    if len(p) >= 10: 
                        sat_id = p[1]
                        clock_bias_us = float(p[9]) * 1e6
                        # CLK 파일 결측치 원천 차단
                        if abs(clock_bias_us) < 900000.0:
                            rows.append([sat_id, clock_bias_us])
            
            df = pd.DataFrame(rows, columns=['Satellite_ID', 'Clock_Bias_Raw_us'])
            
            if not df.empty:
                # K-PROTOCOL 보정 연산
                df['Calibrated_Bias_us'] = df['Clock_Bias_Raw_us'] / S_EARTH
                df['Temporal_Residual_us'] = df['Clock_Bias_Raw_us'] - df['Calibrated_Bias_us']
                
                st.subheader("Data Calculation Results (SP3/CLK)")
                st.write("Extracting Temporal Residuals by applying K-PROTOCOL base metric (S_earth) to the Raw Clock Bias.")
                
                # 1. 막대 그래프 (전체 위성의 시간 잔차 평균)
                df_mean = df.groupby('Satellite_ID', as_index=False)['Temporal_Residual_us'].mean()
                fig_bar = px.bar(df_mean, x='Satellite_ID', y='Temporal_Residual_us',
                             title="Average Temporal Residuals per Satellite (μs)",
                             labels={'Temporal_Residual_us': 'Temporal Residual (μs)', 'Satellite_ID': 'Satellite ID'},
                             template="plotly_white",
                             color_discrete_sequence=["#0056B3"])
                st.plotly_chart(fig_bar, use_container_width=True)
                
                st.divider()
                
                # 2. 개별 위성 선택 이중 선형 그래프 (SI vs K-PROTOCOL)
                st.markdown("#### Detailed Analysis: SI Standard vs K-PROTOCOL")
                unique_sats = df['Satellite_ID'].unique()
                selected_sat = st.selectbox("Select a Satellite ID to view timeline comparison:", unique_sats)
                
                # 선택한 위성 데이터만 필터링
                df_sat = df[df['Satellite_ID'] == selected_sat].reset_index(drop=True)
                
                # 두 개의 선형 그래프 출력 (Raw vs Calibrated)
                fig_line = px.line(df_sat, y=['Clock_Bias_Raw_us', 'Calibrated_Bias_us'],
                                 title=f"Clock Bias Comparison for Satellite {selected_sat} (μs)",
                                 labels={'index': 'Data Points (Time)', 'value': 'Clock Bias (μs)', 'variable': 'Standard'},
                                 template="plotly_white",
                                 color_discrete_map={'Clock_Bias_Raw_us': '#6C757D', 'Calibrated_Bias_us': '#E63946'})
                
                # 범례 이름 깔끔하게 변경
                newnames = {'Clock_Bias_Raw_us': 'SI Standard (Raw)', 'Calibrated_Bias_us': 'K-PROTOCOL (Calibrated)'}
                fig_line.for_each_trace(lambda t: t.update(name = newnames[t.name], legendgroup = newnames[t.name], hovertemplate = t.hovertemplate.replace(t.name, newnames[t.name])))
                fig_line.update_traces(mode='lines+markers')
                
                st.plotly_chart(fig_line, use_container_width=True)
                
                # 에러 방지 데이터 표 출력
                format_dict_sp3 = {'Clock_Bias_Raw_us': '{:.6f}', 'Calibrated_Bias_us': '{:.6f}', 'Temporal_Residual_us': '{:.6f}'}
                st.dataframe(df.style.format(format_dict_sp3), use_container_width=True)

    # ==========================================
    # 8. Philosophical Popup & Export
    # ==========================================
    if not df.empty and file_type_flag:
        st.markdown(f"<div class='philosophical-quote'>\"{t['insight_msg']}\"</div>", unsafe_allow_html=True)
        
        pdf_bytes = create_integrity_report(df, file_type_flag, r_sq, max_res)
        st.download_button(
            label="Download Analytical Report (PDF)",
            data=pdf_bytes,
            file_name=f"K_PROTOCOL_Report_{datetime.datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            type="primary"
        )

# ==========================================
# 9. Footer
# ==========================================
st.divider()
c_foot1, c_foot2 = st.columns([2, 1])

with c_foot1:
    st.markdown("**Citation**")
    st.code("CK (CitizenKorea). (2026). K-PROTOCOL: Grand Unification via Sloc. Zenodo. https://doi.org/10.5281/zenodo.18976813", language="text")

with c_foot2:
    st.markdown("**Collaboration & Inquiries**")
    st.markdown("Email: [estake@naver.com](mailto:estake@naver.com)")
    st.markdown("Author: CK (CitizenKorea)")

st.caption("© 2026. Patent Pending: The K-PROTOCOL algorithm and related papers are patent pending.")
