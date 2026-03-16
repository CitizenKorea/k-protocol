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
# 2. Page Configuration & CSS Styling
# ==========================================
st.set_page_config(page_title="K-PROTOCOL Omni Analysis Center", layout="wide", page_icon="🛰️")

st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; color: #212529; }
    .metric-box { background-color: #FFFFFF; padding: 20px; border-left: 4px solid #0056B3; border-radius: 5px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .metric-title { font-size: 14px; color: #6C757D; text-transform: uppercase; letter-spacing: 1px; font-weight: bold; }
    .metric-value { font-size: 24px; font-weight: 700; color: #212529; }
    .link-box a { color: #0056B3; text-decoration: none; font-weight: bold; }
    hr { border-color: #DEE2E6; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. 깃허브 실시간 데이터 연동 (조작 없음)
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
        'bg_title': "⚖️ 왜 기존 오차가 발생하는가? (SI 단위계의 순환논리와 한계)",
        'bg_text': r"""
현재 정밀 데이터에서 발생하는 정체 모를 오차들은 **'순환논리에 빠진 기존 SI 단위계'**를 그대로 사용하기 때문에 발생합니다. 빛의 속도로 거리를 정의하고, 다시 그 거리로 빛의 속도를 측정하는 모순된 체계는 지구 중력에 의한 시공간 왜곡을 보정할 수 없습니다.

K-PROTOCOL은 절대 기하학적 상수인 $S_{earth}$와 보정 광속 $c_k$를 통해 이 순환논리를 타파합니다.
나아가, 각 지점의 고도($h$)와 지구 반경($R$)에 따른 **국소 중력($g_{loc}$)**을 반영하여 개별 척도 계수($S_{loc}$)를 산출함으로써 가장 정밀하고 진실된 물리 값을 도출합니다.
        """,
        'upload_prompt': "SNX (통합 솔루션 포함), SP3, CLK 파일을 드래그 앤 드롭 하십시오",
        'insight_msg': "이 수치는 수학적 사실입니다. 정답은 오직 데이터 속에 있습니다.",
    },
    'ENG': {
        'title': "K-PROTOCOL Omni Analysis Center",
        'subtitle': "Let the data speak. Judge for yourself.",
        'bg_title': "⚖️ Why Do Errors Occur? (Circular Logic and Limitations of SI Units)",
        'bg_text': r"""
The persistent errors found in modern precision data arise from the **'circular logic of the conventional SI unit system.'** A system that defines distance by the speed of light, and then measures light by that same distance, is fundamentally incapable of calibrating the geometric distortions of spacetime.

K-PROTOCOL breaks this cycle utilizing the universal geometric constant $S_{earth}$ and the calibrated speed of light $c_k$.
Furthermore, by accounting for the **local gravity ($g_{loc}$)** at each point and altitude ($h$) to derive the specific metric factor ($S_{loc}$), it reveals the most precise and authentic physical values.
        """,
        'upload_prompt': "Drag and drop SNX (including ITRF combined), SP3, or CLK files",
        'insight_msg': "These figures are mathematical facts. The answer lies within the data.",
    }
}
t = i18n[lang]

# ==========================================
# 5. Header & Trust Metrics
# ==========================================
col_title, col_lang = st.columns([8, 1])
with col_title:
    st.markdown(f"# {t['title']}")
    st.markdown(f"#### {t['subtitle']}")
with col_lang:
    selected_lang = st.radio("Language", ["ENG", "KOR"], label_visibility="collapsed", horizontal=True)
    if selected_lang != st.session_state['lang']:
        st.session_state['lang'] = selected_lang
        st.rerun()

st.divider()

with st.expander(t['bg_title'], expanded=True):
    st.info(t['bg_text'])

c1, c2, c3 = st.columns([1, 1, 2])
with c1:
    st.markdown(f'<div class="metric-box"><div class="metric-title">GITHUB STARS</div><div class="metric-value">{real_stars}</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-box"><div class="metric-title">GITHUB FORKS</div><div class="metric-value">{real_forks}</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown("**🔗 Detailed Theoretical Evidence & References**")
    st.markdown("<div class='link-box'>📄 <a href='https://doi.org/10.5281/zenodo.18976813' target='_blank'>Full Theoretical Background (Zenodo)</a></div>", unsafe_allow_html=True)

st.divider()

# ==========================================
# 6. PDF Generation (Data Epoch 포함 버전)
# ==========================================
def create_integrity_report(df, file_type, file_name, data_epoch, r_sq=None, max_res=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(190, 10, "K-PROTOCOL Analytical Integrity Report", 0, 1, 'C')
    pdf.ln(5)
    
    pdf.set_font("helvetica", '', 10)
    pdf.cell(190, 8, f"Target Source File: {file_name}", 0, 1, 'L')
    pdf.cell(190, 8, f"Data Epoch (Observation Time): {data_epoch}", 0, 1, 'L')
    pdf.cell(190, 8, f"Report Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1, 'L')
    pdf.cell(190, 8, f"Algorithm: K-PROTOCOL (Patent Pending)", 0, 1, 'L')
    pdf.ln(8)
    
    if file_type == 'SNX' and not df.empty:
        pdf.set_font("helvetica", 'B', 12)
        pdf.cell(190, 10, "[ 3D Spatial Metric Calibration Results ]", 0, 1, 'L')
        pdf.set_font("helvetica", '', 10)
        if max_res is not None: pdf.cell(190, 8, f"Calculated Max Residual: {max_res:.6f} m", 0, 1, 'L')
        if r_sq is not None: pdf.cell(190, 8, f"Calculated Correlation (R-squared): {r_sq:.7f}%", 0, 1, 'L')
        pdf.ln(5); pdf.set_font("helvetica", 'B', 9)
        pdf.cell(40, 10, "Station ID", 1, 0, 'C'); pdf.cell(40, 10, "Altitude (m)", 1, 0, 'C'); pdf.cell(50, 10, "SI Distance (m)", 1, 0, 'C'); pdf.cell(50, 10, "K-Residual (m)", 1, 1, 'C')
        pdf.set_font("helvetica", '', 8)
        for _, row in df.head(40).iterrows():
            pdf.cell(40, 8, str(row['ID'])[:15], 1, 0, 'C'); pdf.cell(40, 8, f"{row['Altitude']:.2f}", 1, 0, 'C'); pdf.cell(50, 8, f"{row['SI_Dist']:.2f}", 1, 0, 'C'); pdf.cell(50, 8, f"{row['Residual']:.6f}", 1, 1, 'C')

    elif file_type == 'SP3' and not df.empty:
        pdf.set_font("helvetica", 'B', 12)
        pdf.cell(190, 10, "[ Absolute Time Synchronization Results ]", 0, 1, 'L')
        pdf.set_font("helvetica", '', 10)
        avg_residual = df['Temporal_Residual_us'].abs().mean()
        pdf.cell(190, 8, f"Analyzed Satellites: {len(df['Satellite_ID'].unique())}", 0, 1, 'L')
        pdf.cell(190, 8, f"Average Temporal Residual: {avg_residual:.6f} us", 0, 1, 'L')
        pdf.ln(5); pdf.set_font("helvetica", 'B', 9)
        pdf.cell(30, 10, "Satellite ID", 1, 0, 'C'); pdf.cell(50, 10, "Raw Clock Bias (us)", 1, 0, 'C'); pdf.cell(50, 10, "Calibrated Bias (us)", 1, 0, 'C'); pdf.cell(50, 10, "Temporal Residual (us)", 1, 1, 'C')
        pdf.set_font("helvetica", '', 8)
        for _, row in df.head(40).iterrows():
            pdf.cell(30, 8, str(row['Satellite_ID'])[:15], 1, 0, 'C'); pdf.cell(50, 8, f"{row['Clock_Bias_Raw_us']:.6f}", 1, 0, 'C'); pdf.cell(50, 8, f"{row['Calibrated_Bias_us']:.6f}", 1, 0, 'C'); pdf.cell(50, 8, f"{row['Temporal_Residual_us']:.6f}", 1, 1, 'C')

    out = pdf.output(dest='S')
    return out.encode('latin-1') if isinstance(out, str) else bytes(out)

# ==========================================
# 7. Dynamic Analysis Engine
# ==========================================
uploaded_file = st.file_uploader(t['upload_prompt'], type=["snx", "sp3", "clk", "gz", "z"])

if uploaded_file:
    fname = uploaded_file.name.lower()
    
    # .Z 확장자 안전장치 (Unix Compress)
    if fname.endswith('.z') and not fname.endswith('.gz'):
        st.error("🚨 **[포맷 경고]** `.Z` (Unix Compress) 압축 파일이 감지되었습니다! 파이썬 기본 환경의 안정성을 위해, 반디집 등을 이용하여 압축을 해제한 후 **원본 `.snx` 파일**이나 **`.gz` 포맷**으로 다시 업로드해 주십시오.")
        st.stop()

    df = pd.DataFrame()
    file_type_flag = None; r_sq = None; max_res = None
    data_epoch = "Time/Epoch data not explicitly found in header"
    
    with st.spinner("Analyzing data integrity & Extracting Data Epoch..."):
        
        # --- SNX Parser (Multi-Technique & Spatial) ---
        if ".snx" in fname:
            file_type_flag = 'SNX'
            f = gzip.open(uploaded_file, 'rt', encoding='utf-8', errors='ignore') if fname.endswith('.gz') else io.TextIOWrapper(uploaded_file, encoding='utf-8', errors='ignore')
            
            capture_site = False
            capture_est = False
            site_tech_map = {} 
            snx_data = {}      
            
            for line in f:
                if line.startswith('%=SNX'):
                    data_epoch = f"SNX Base Header [{line.strip()[:50]}]"
                
                if line.startswith('+SITE/ID'): capture_site = True; continue
                if line.startswith('-SITE/ID'): capture_site = False; continue
                
                if line.startswith('+SOLUTION/ESTIMATE'): capture_est = True; continue
                if line.startswith('-SOLUTION/ESTIMATE'): capture_est = False; break
                
                if capture_site and not line.startswith('*') and len(line) > 20:
                    code = line[1:5].strip()
                    pt = line[6:8].strip()
                    tech = line[19:20].strip() # L(SLR), R(VLBI), P(GNSS)
                    site_tech_map[(code, pt)] = tech
                    
                if capture_est and not line.startswith('*'):
                    if any(a in line for a in ['STAX', 'STAY', 'STAZ']):
                        try:
                            est_type = line[7:11].strip()
                            code = line[14:18].strip()
                            pt = line[19:21].strip()
                            val = float(line[47:68])
                            
                            tech = site_tech_map.get((code, pt), 'Unknown')
                            
                            if code not in snx_data: snx_data[code] = {}
                            if tech not in snx_data[code]: snx_data[code][tech] = {}
                            snx_data[code][tech][est_type] = val
                        except:
                            pass
            
            rows_spatial = []
            rows_multi = []
            tech_names = {'L': 'SLR', 'R': 'VLBI', 'P': 'GNSS', 'D': 'DORIS'}
            
            for code, tech_dict in snx_data.items():
                valid_techs = {tech: coords for tech, coords in tech_dict.items() if all(k in coords for k in ['STAX', 'STAY', 'STAZ'])}
                
                # 기본 공간 왜곡 분석용 (가장 대표적인 기술 1개만 추출)
                if valid_techs:
                    rep_tech = list(valid_techs.keys())[0]
                    c = valid_techs[rep_tech]
                    R_SI = np.sqrt(c['STAX']**2 + c['STAY']**2 + c['STAZ']**2)
                    alt = R_SI - R_EARTH
                    g_loc = G_SI * ((R_EARTH / R_SI)**2)
                    s_loc = (np.pi**2) / g_loc
                    rows_spatial.append([code, rep_tech, R_SI, alt, g_loc, s_loc])
                
                # 다중 기술 교차 관측소 (Co-location) 비교
                if len(valid_techs) >= 2:
                    tech_list = list(valid_techs.keys())
                    for i in range(len(tech_list)):
                        for j in range(i+1, len(tech_list)):
                            t1, t2 = tech_list[i], tech_list[j]
                            c1, c2 = valid_techs[t1], valid_techs[t2]
                            r1 = np.sqrt(c1['STAX']**2 + c1['STAY']**2 + c1['STAZ']**2)
                            r2 = np.sqrt(c2['STAX']**2 + c2['STAY']**2 + c2['STAZ']**2)
                            
                            avg_r = (r1 + r2) / 2
                            g_loc = G_SI * ((R_EARTH / avg_r)**2)
                            s_loc = (np.pi**2) / g_loc
                            
                            si_diff = abs(r1 - r2)
                            k_r1 = r1 / s_loc
                            k_r2 = r2 / s_loc
                            k_diff = abs(k_r1 - k_r2)
                            
                            rows_multi.append([code, f"{tech_names.get(t1, t1)} vs {tech_names.get(t2, t2)}", r1, r2, si_diff, s_loc, k_r1, k_r2, k_diff])

            df = pd.DataFrame(rows_spatial, columns=['ID', 'Technique', 'SI_Dist', 'Altitude', 'g_loc', 'S_loc'])
            df_multi = pd.DataFrame(rows_multi, columns=['Station_ID', 'Compare', 'R_Tech1 (m)', 'R_Tech2 (m)', 'SI_Discrepancy (m)', 'S_loc', 'K_Tech1 (m)', 'K_Tech2 (m)', 'K_Discrepancy (m)'])

            if not df.empty:
                df['K_Dist'] = df['SI_Dist'] / df['S_loc']; df['Residual'] = df['SI_Dist'] - df['K_Dist']
                max_res = df['Residual'].abs().max()
                corr, _ = pearsonr(df['Altitude'], df['Residual']); r_sq = (corr**2) * 100
                
                # 1. 다중 기술 교차 분석 UI
                if not df_multi.empty:
                    st.success(f"✅ 발견 완료! 동일 관측소 내에서 다중 기술(SLR, VLBI 등)이 겹치는 {len(df_multi)}건의 데이터를 나노-추출했습니다.")
                    st.subheader("🔭 1. [결정적 증거] Multi-Technique Co-location Analysis")
                    st.markdown("현대 측지학이 설명하지 못하는 **SLR(레이저)과 VLBI(전파) 등 측정 기술 간의 거리 척도 불일치(Scale Discrepancy)**입니다.")
                    st.dataframe(df_multi.style.format({
                        'R_Tech1 (m)': '{:,.4f}', 'R_Tech2 (m)': '{:,.4f}', 
                        'SI_Discrepancy (m)': '{:,.6f}', 'S_loc': '{:.7f}',
                        'K_Tech1 (m)': '{:,.4f}', 'K_Tech2 (m)': '{:,.4f}', 'K_Discrepancy (m)': '{:,.6f}'
                    }), use_container_width=True)
                    st.info("💡 **증명 가이드**: 위 표의 `SI_Discrepancy`는 동일한 장소임에도 측정 기술에 따라 발생하는 왜곡 오차입니다. 논문의 전략 1에 따라, $S_{loc}$ 텐서 변환이 이 불일치를 어떻게 재해석하는지 확인할 수 있습니다.")

                st.divider()
                st.subheader("🌐 2. Spatial Metric Calibration Results (All Stations)")
                
                # 2. 고도 vs 잔차 산점도
                st.plotly_chart(px.scatter(df, x='Altitude', y='Residual', hover_data=['ID', 'Technique'], trendline="ols", trendline_color_override="#0056B3", title=f"Actual Correlation (Altitude vs Residual) | R² = {r_sq:.7f}%", template="plotly_white"), use_container_width=True)

        # --- SP3/CLK Parser (Temporal) ---
        elif any(x in fname for x in ['.sp3', '.clk']):
            file_type_flag = 'SP3'; rows = []
            f = gzip.open(uploaded_file, 'rt') if fname.endswith('.gz') else io.TextIOWrapper(uploaded_file)
            for line in f:
                if "sp3" in fname and line.startswith('* ') and "not explicitly found" in data_epoch:
                    data_epoch = f"SP3 Start Epoch: {line[2:25].strip()}"
                if "clk" in fname and line.startswith('AS ') and "not explicitly found" in data_epoch:
                    p = line.split()
                    if len(p) >= 8:
                        data_epoch = f"CLK First Epoch: {p[2]}-{p[3]}-{p[4]} {p[5]}:{p[6]}:{p[7]}"
                
                if "sp3" in fname and line.startswith('P'):
                    try:
                        s, b = line[1:4].strip(), float(line[46:60])
                        if abs(b) < 900000.0: rows.append([s, b])
                    except: pass
                elif "clk" in fname and line.startswith('AS'):
                    p = line.split()
                    if len(p) >= 10:
                        s, b_us = p[1], float(p[9])*1e6
                        if abs(b_us) < 900000.0: rows.append([s, b_us])
            
            df = pd.DataFrame(rows, columns=['Satellite_ID', 'Clock_Bias_Raw_us'])
            if not df.empty:
                df['Calibrated_Bias_us'] = df['Clock_Bias_Raw_us'] / S_EARTH; df['Temporal_Residual_us'] = df['Clock_Bias_Raw_us'] - df['Calibrated_Bias_us']
                st.subheader("Temporal Synchronization Results (SP3/CLK)")
                df_m = df.groupby('Satellite_ID', as_index=False)['Temporal_Residual_us'].mean()
                st.plotly_chart(px.bar(df_m, x='Satellite_ID', y='Temporal_Residual_us', title="Average Temporal Residuals (μs)", template="plotly_white"), use_container_width=True)
                st.divider(); st.markdown("#### Detailed Satellite Timeline Comparison")
                sel_sat = st.selectbox("Select Satellite ID:", df['Satellite_ID'].unique())
                df_sat = df[df['Satellite_ID'] == sel_sat].reset_index(drop=True)
                st.plotly_chart(px.line(df_sat, y=['Clock_Bias_Raw_us', 'Calibrated_Bias_us'], title=f"Clock Bias: SI Standard vs K-PROTOCOL ({sel_sat})", template="plotly_white", color_discrete_map={'Clock_Bias_Raw_us': '#6C757D', 'Calibrated_Bias_us': '#E63946'}), use_container_width=True)

    # ==========================================
    # 8. Export & Verification 
    # ==========================================
    if not df.empty and file_type_flag:
        st.info(f"💡 {t['insight_msg']}")
        st.download_button(label="📄 Download Analytical Integrity Report (PDF)", 
                           data=create_integrity_report(df, file_type_flag, uploaded_file.name, data_epoch, r_sq, max_res), 
                           file_name=f"K_PROTOCOL_Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", 
                           mime="application/pdf", type="primary")

# ==========================================
# 9. Footer 
# ==========================================
st.divider()
c_foot1, c_foot2 = st.columns([2, 1])

with c_foot1:
    st.markdown("**📝 Citation (논문 인용)**")
    st.code("CK (CitizenKorea). (2026). K-PROTOCOL: Grand Unification via Sloc. Zenodo.", language="text")

with c_foot2:
    st.markdown("**🤝 Collaboration & Inquiries**")
    st.markdown("Email: [estake@naver.com](mailto:estake@naver.com)")

st.caption("© 2026. Patent Pending: The K-PROTOCOL algorithm and related mathematical verifications are strictly patent pending.")
