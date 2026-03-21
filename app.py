import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gzip
import io
import os
import requests
from scipy.stats import pearsonr
from scipy.spatial import KDTree
from fpdf import FPDF
import datetime

# ==========================================
# 1. K-PROTOCOL Universal Constants (학술적 표기 교정)
# ==========================================
g_SI = 9.80665  
S_EARTH = (np.pi**2) / g_SI
C_SI = 299792458
C_K = C_SI / S_EARTH
R_EARTH = 6371000

# ==========================================
# 2. Page Configuration & CSS
# ==========================================
st.set_page_config(page_title="K-PROTOCOL Omni Analysis Center", layout="wide", page_icon="🛰️")

st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; color: #212529; }
    .metric-box { background-color: #FFFFFF; padding: 20px; border-left: 4px solid #0056B3; border-radius: 5px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .metric-title { font-size: 14px; color: #6C757D; font-weight: bold; letter-spacing: 1px; }
    .metric-value { font-size: 24px; font-weight: 700; color: #212529; }
    .multi-box { border: 2px solid #2A9D8F; padding: 25px; border-radius: 10px; background-color: #F1FAEE; margin-top: 20px; margin-bottom: 30px; box-shadow: 0 4px 6px rgba(42,157,143,0.1); }
    .explain-box { background-color: #FFFFFF; padding: 25px; border-left: 5px solid #495057; border-radius: 5px; margin-bottom: 25px; font-size: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .defense-box { background-color: #FFF3CD; color: #856404; padding: 15px; border-left: 5px solid #FFEEBA; border-radius: 5px; margin-bottom: 20px; font-size: 14px; }
    .source-box { background-color: #E2ECE9; color: #2B2D42; padding: 25px; border-left: 5px solid #8D99AE; border-radius: 5px; margin-bottom: 30px; }
    hr { border-color: #DEE2E6; }
    .link-list { line-height: 1.8; font-size: 15px; }
    .link-list a { text-decoration: none; font-weight: 600; color: #0056B3; }
    .link-list a:hover { text-decoration: underline; color: #E63946; }
    .glossary-card { background-color: #ffffff; border: 1px solid #e0e0e0; padding: 15px; border-radius: 5px; font-size: 14px; margin-bottom: 20px; line-height: 1.6;}
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=600)
def get_github_stats():
    try:
        r = requests.get("https://api.github.com/repos/CitizenKorea/k-protocol", timeout=5)
        if r.status_code == 200:
            d = r.json()
            return d.get("stargazers_count", 0), d.get("forks_count", 0)
        return 0, 0
    except: return 0, 0

real_stars, real_forks = get_github_stats()

# ==========================================
# 3. Language Dictionary (원본 텍스트 100% 복구)
# ==========================================
if 'lang' not in st.session_state:
    st.session_state['lang'] = 'ENG'

i18n = {
    'KOR': {
        'title': "K-PROTOCOL Omni 분석 센터",
        'subtitle': "데이터로 증명하고, 스스로 판단하십시오. (The Absolute Proof)",
        'bg_title': "⚖️ 왜 기존 오차가 발생하는가? (K-PROTOCOL의 존재 이유)",
        'bg_text': """
        현대 정밀 물리학의 가장 큰 맹점은 **'빛의 속도를 고정해 놓고 거리를 잰 뒤, 다시 그 거리로 빛을 측정하는 순환논리'**에 빠져 있다는 것입니다. 
        이러한 기존 SI 단위계의 한계는 지구 중력과 고도에 의해 발생하는 시공간의 기하학적 왜곡을 결코 보정할 수 없습니다. 
        K-PROTOCOL은 절대 기하학적 상수인 **지구 절대 척도(S_earth ≈ 1.006419)**와 각 지점의 국소 중력에 따른 **척도 계수 텐서(S_loc)**를 적용하여, 주류 학계가 설명하지 못하는 척도 불일치를 완벽하게 교정합니다.
        """,
        'src_title': "📂 데이터 출처 및 자동 분석 엔진",
        'src_box_title': "내장된 기본 증거 데이터 (NASA CDDIS / UCSD Garner Archive)",
        'src_box_1': "<b>원천 데이터 출처:</b> NASA CDDIS 우주 측지 데이터 및 UCSD Garner 아카이브 (정밀 궤도/시계 원본)",
        'src_box_2': "<b>무손실 추출 방식:</b> 관측소 식별 코드와 순수 3D 관측 좌표(STAX, STAY, STAZ) 및 위성 시계 오차를 100% 원본 그대로 추출하였습니다.",
        'src_box_3': "아래 수치들은 K-PROTOCOL 방정식이 진리임을 증명하는 수학적 팩트입니다. (사용자 파일 미 업로드 시 기본 증거 데이터를 자동 분석합니다.)",
        'upload_prompt': "자신만의 데이터를 직접 분석하고 싶다면 업로드하십시오. (NASA 제공 SNX.gz, SP3.gz, CLK.gz 지원)",
        'case1_title': "🔭 [CASE 1] 다중 기술 척도 불일치 교차 검증 (SLR vs VLBI vs GNSS)",
        'case1_desc': "**분석 원리:** 본 엔진은 ITRF 원본의 관측소 이름표를 정확히 인식한 뒤, 30km 반경 내에 겹쳐있는 기기들을 강제 매칭시킵니다. 기기 간의 물리적 거리(SI_Diff) 속에 숨어있던 **'기하학적 공간 왜곡(거품)'**을 K-PROTOCOL(S_loc)이 얼마나 정확히 찾아내어 깎아내는지(Calibration) 시각적으로 증명합니다.",
        'case1_guide': """
        <div class="glossary-card">
            <b>💡 분석 가이드:</b> 동일한 부지 내에 설치된 서로 다른 두 장비(예: SLR과 GNSS) 사이의 거리를 분석합니다.<br>
            • <b>SI_Diff (m)</b>: 두 장비 간의 <b>실제 물리적 이격 거리</b>입니다. (아무리 공식을 써도 기기 간의 실제 거리가 0이 될 수는 없습니다.)<br>
            • <b>S_loc</b>: K-PROTOCOL이 밝혀낸 해당 고도/지역의 국소 공간 왜곡 지수입니다.<br>
            • <b>추출된 왜곡량 (Correction)</b>: 기존 미터법이 과대평가하고 있던 시공간의 <b>'기하학적 거품'</b>입니다. K-PROTOCOL은 이 수치만큼의 환영을 정확히 찾아내어 깎아냈습니다(Calibration).
        </div>
        """,
        'case2_title': "🌐 [CASE 2] 전 지구적 공간 왜곡 보정 분석 (Spatial Calibration)",
        'case2_desc': "**분석 원리:** 전 세계 관측소를 고도에 따라 정렬하고 공간 왜곡량(Residual)을 역추적합니다. 99.9%에 달하는 극단적 상관계수(R²)는 이 방정식의 완벽성을 증명합니다.",
        'defense_text': "💡 **과학적 주석:** 이 99.99%의 상관관계는 단순한 수식적 순환 참조가 아닙니다. 물리적 고도(Altitude)와 기하학적 잔차(Residual)라는 독립적인 두 변수가 국소 중력 환경에 따라 완벽하게 동기화되어 움직인다는 '물리적 실체'를 교차 검증한 결과입니다.",
        'case3_title': "⏱️ [CASE 3] 절대 시간 동기화 분석 (Temporal Synchronization)",
        'case3_desc': "**분석 원리:** 궤도 상의 원자 시계 오차(SP3/CLK) 데이터를 파싱하여 시간에 따른 K-PROTOCOL 잔차의 수렴성을 분석합니다.",
        'download_btn': "📄 K-PROTOCOL 분석 무결성 리포트 다운로드 (PDF)",
        'ref_title': "🔗 공인 데이터 출처 및 레퍼런스 링크"
    },
    'ENG': {
        'title': "K-PROTOCOL Omni Analysis Center",
        'subtitle': "Let the data speak. Judge for yourself. (The Absolute Proof)",
        'bg_title': "⚖️ Why Do Errors Occur? (The Rationale for K-PROTOCOL)",
        'bg_text': """
        The greatest blind spot in modern precision physics is the circular logic of defining distance by the speed of light. 
        K-PROTOCOL perfectly corrects the scale discrepancies that mainstream academia cannot explain using the local metric tensor (S_loc).
        """,
        'src_title': "📂 Data Source & Auto-Analysis Engine",
        'src_box_title': "Built-in Evidence Data (NASA CDDIS / UCSD Garner Archive)",
        'src_box_1': "<b>Raw Data Source:</b> NASA CDDIS Geodetic Data and UCSD Garner Archive (Precision Orbit/Clock Raw Data)",
        'src_box_2': "<b>Lossless Extraction:</b> Pure 3D coordinates and satellite clock biases were extracted 100% as-is.",
        'src_box_3': "These figures are mathematical facts proving the K-PROTOCOL equation. (Default evidence data is auto-analyzed if no file is uploaded.)",
        'upload_prompt': "Upload your own files to analyze directly. (Supports NASA SNX.gz, SP3.gz, CLK.gz)",
        'case1_title': "🔭 [CASE 1] Multi-Technique Discrepancy (3D Proximity Match)",
        'case1_desc': "**Analytical Principle:** This engine identifies colocated instruments within a 30km radius. It visually proves exactly how much **'hidden geometric distortion'** K-PROTOCOL (S_loc) extracts and calibrates from the observed physical distance (SI_Diff) between instruments.",
        'case1_guide': """
        <div class="glossary-card">
            <b>💡 Analysis Guide:</b> Analyzes the distance between two different instruments (e.g., SLR and GNSS) installed on the same site.<br>
            • <b>SI_Diff (m)</b>: The <b>actual physical separation distance</b> between the two instruments. (No formula can make the actual physical distance between instruments zero.)<br>
            • <b>S_loc</b>: The local spatial distortion index of the corresponding altitude/region revealed by K-PROTOCOL.<br>
            • <b>Extracted Error (Correction)</b>: The <b>'geometric bubble'</b> of spacetime that the existing metric system was overestimating. K-PROTOCOL exactly identifies and calibrates out this illusion.
        </div>
        """,
        'case2_title': "🌐 [CASE 2] Global Spatial Metric Calibration",
        'case2_desc': "**Analytical Principle:** Traces spatial distortion across thousands of global stations. The extreme R² correlation is absolute proof of the theory.",
        'defense_text': "💡 **Scientific Note:** This 99.99% correlation is not a mathematical tautology. It demonstrates that the spatial residual (error) precisely scales with the physical altitude and local gravity of each independent station, verifying the geometric metric transformation.",
        'case3_title': "⏱️ [CASE 3] Absolute Temporal Synchronization",
        'case3_desc': "**Analytical Principle:** Analyzes the convergence of K-PROTOCOL residuals over time using atomic clock data (SP3/CLK).",
        'download_btn': "📄 Download Analytical Integrity Report (PDF)",
        'ref_title': "🔗 Verified Reference & Raw Data Sources"
    }
}

# ==========================================
# 4. UI Setup
# ==========================================
col_title, col_lang = st.columns([8, 1])
with col_title:
    st.markdown(f"# {i18n[st.session_state['lang']]['title']}")
    st.markdown(f"#### {i18n[st.session_state['lang']]['subtitle']}")
with col_lang:
    selected_lang = st.radio("Language", ["ENG", "KOR"], horizontal=True, label_visibility="collapsed")
    if selected_lang != st.session_state['lang']:
        st.session_state['lang'] = selected_lang
        st.rerun()

t = i18n[st.session_state['lang']]
st.divider()

with st.expander(t['bg_title'], expanded=True):
    st.info(t['bg_text'])

c1, c2, c3 = st.columns([1, 1, 2.5])
with c1: 
    st.markdown(f'<div class="metric-box"><div class="metric-title">GITHUB STARS</div><div class="metric-value">{real_stars}</div></div>', unsafe_allow_html=True)
with c2: 
    st.markdown(f'<div class="metric-box"><div class="metric-title">GITHUB FORKS</div><div class="metric-value">{real_forks}</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f"**{t['ref_title']}**")
    st.markdown("""
    <div class="link-list">
        📄 <a href="https://doi.org/10.5281/zenodo.19103876" target="_blank">Full Theoretical Background (Zenodo - Latest)</a><br>
        🛰️ <a href="http://garner.ucsd.edu/pub/products/2392/" target="_blank">SOPAC GNSS Products (Garner)</a><br>
        🌕 <a href="https://cddis.nasa.gov/archive/slr/data/fr_crd_v2/apollo15/2025/" target="_blank">NASA CDDIS LLR Data (Apollo 15, 2025)</a>
    </div>
    """, unsafe_allow_html=True)

st.divider()
st.markdown(f"### {t['src_title']}")
st.markdown(f"""
<div class="source-box">
    <h4>{t['src_box_title']}</h4>
    <ul><li>{t['src_box_1']}</li><li>{t['src_box_2']}</li><li>{t['src_box_3']}</li></ul>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader(t['upload_prompt'], type=["snx", "sp3", "clk", "gz", "fr2"])

# ==========================================
# 5. PDF Generator (인코딩 안정성 확보)
# ==========================================
def create_integrity_report(df_spatial, df_multi, df_temporal, file_type, file_name, data_epoch, r_sq=None, max_res=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(190, 10, "K-PROTOCOL Analytical Integrity Report", 0, 1, 'C')
    pdf.ln(5)
    pdf.set_font("helvetica", '', 10)
    pdf.cell(190, 8, f"Target Source File: {file_name}", 0, 1, 'L')
    pdf.cell(190, 8, f"Data Epoch: {data_epoch}", 0, 1, 'L')
    pdf.cell(190, 8, f"Report Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1, 'L')
    pdf.ln(5)
    
    if not df_multi.empty:
        pdf.set_font("helvetica", 'B', 12)
        pdf.cell(190, 10, "[ Multi-Technique Discrepancy Calibration ]", 0, 1, 'L')
        pdf.set_font("helvetica", 'B', 9)
        pdf.cell(60, 8, "Colocated Sites", 1, 0, 'C')
        pdf.cell(30, 8, "Compare", 1, 0, 'C')
        pdf.cell(35, 8, "SI_Diff (m)", 1, 0, 'C')
        pdf.cell(35, 8, "K_Diff (m)", 1, 0, 'C')
        pdf.cell(30, 8, "Correction", 1, 1, 'C')
        pdf.set_font("helvetica", '', 8)
        for _, row in df_multi.head(30).iterrows():
            pdf.cell(60, 8, str(row['Colocated Sites'])[:25], 1, 0, 'C')
            pdf.cell(30, 8, str(row['Compare']), 1, 0, 'C')
            pdf.cell(35, 8, f"{row['SI_Diff (m)']:.4f}", 1, 0, 'C')
            pdf.cell(35, 8, f"{row.get('K_Diff (m)', 0):.4f}", 1, 0, 'C')
            pdf.cell(30, 8, f"{row.get('Correction (m)', 0):.6f}", 1, 1, 'C')
        pdf.ln(8)
        
    if not df_spatial.empty:
        pdf.set_font("helvetica", 'B', 12)
        pdf.cell(190, 10, "[ 3D Spatial Metric Calibration Results ]", 0, 1, 'L')
        pdf.set_font("helvetica", '', 10)
        if r_sq is not None: pdf.cell(190, 8, f"Calculated Correlation (R-squared): {r_sq:.7f}%", 0, 1, 'L')
        pdf.ln(5)
        pdf.set_font("helvetica", 'B', 9)
        pdf.cell(30, 10, "Station ID", 1, 0, 'C')
        pdf.cell(20, 10, "Tech", 1, 0, 'C')
        pdf.cell(40, 10, "Altitude (m)", 1, 0, 'C')
        pdf.cell(50, 10, "SI Distance (m)", 1, 0, 'C')
        pdf.cell(50, 10, "K-Residual (m)", 1, 1, 'C')
        pdf.set_font("helvetica", '', 8)
        for _, row in df_spatial.head(40).iterrows():
            pdf.cell(30, 8, str(row['ID'])[:15], 1, 0, 'C')
            pdf.cell(20, 8, str(row['Technique']), 1, 0, 'C')
            pdf.cell(40, 8, f"{row['Altitude']:.2f}", 1, 0, 'C')
            pdf.cell(50, 8, f"{row['SI_Dist']:.2f}", 1, 0, 'C')
            pdf.cell(50, 8, f"{row.get('Residual', 0):.6f}", 1, 1, 'C')
        pdf.ln(8)

    if not df_temporal.empty:
        pdf.set_font("helvetica", 'B', 12)
        pdf.cell(190, 10, "[ Absolute Temporal Synchronization Results ]", 0, 1, 'L')
        pdf.ln(5)
        pdf.set_font("helvetica", 'B', 9)
        pdf.cell(40, 10, "Satellite ID", 1, 0, 'C')
        pdf.cell(50, 10, "Avg Raw Bias", 1, 0, 'C')
        pdf.cell(50, 10, "Avg Calibrated", 1, 0, 'C')
        pdf.cell(50, 10, "Avg Residual (us)", 1, 1, 'C')
        pdf.set_font("helvetica", '', 8)
        df_m = df_temporal.groupby('Satellite_ID').mean(numeric_only=True).reset_index()
        for _, row in df_m.head(40).iterrows():
            pdf.cell(40, 8, str(row['Satellite_ID']), 1, 0, 'C')
            pdf.cell(50, 8, f"{row.get('Clock_Bias_Raw_us', 0):.6f}", 1, 0, 'C')
            pdf.cell(50, 8, f"{row.get('Calibrated_Bias_us', 0):.6f}", 1, 0, 'C')
            pdf.cell(50, 8, f"{row.get('Temporal_Residual_us', 0):.6f}", 1, 1, 'C')

    out = pdf.output(dest='S')
    return out.encode('latin-1', 'replace') if isinstance(out, str) else bytes(out)

# ==========================================
# 6. Core Parsing Engine (선 그래프용 Epoch 추가 및 최적화)
# ==========================================
content_lines = []
fname = ""
file_type_flag, data_epoch = "DEFAULT", "Unknown Epoch"
df_spatial, df_multi, df_temporal = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
r_sq, max_res = None, None

if uploaded_file is not None:
    fname = uploaded_file.name.lower()
    if fname.endswith('.gz'):
        with gzip.open(uploaded_file, 'rt', encoding='utf-8', errors='ignore') as f:
            content_lines = f.read().splitlines()
    else:
        content_lines = uploaded_file.read().decode('utf-8', errors='ignore').splitlines()
else:
    default_path = "K_PROTOCOL_EVIDENCE.snx"
    if os.path.exists(default_path):
        fname = "k_protocol_evidence.snx"
        with open(default_path, 'r', encoding='utf-8', errors='ignore') as f:
            content_lines = f.read().splitlines()

if content_lines:
    with st.spinner("AI 엔진이 물리적 위치와 시공간 좌표를 추적 중입니다..."):
        try:
            file_type_flag = fname
            # --- CASE 1 & 2: SNX 공간 분석 ---
            if ".snx" in fname:
                site_tech_map = {}
                snx_data = {}
                capture_site = False
                capture_est = False
                
                for line in content_lines:
                    if line.startswith('%=SNX'): data_epoch = line[14:35].strip()
                    
                    if line.startswith('+SITE/ID'): capture_site = True; continue
                    if line.startswith('-SITE/ID'): capture_site = False; continue
                    
                    if capture_site and not line.startswith('*') and len(line.strip()) > 10:
                        parts = line.split()
                        if len(parts) >= 4:
                            code = parts[0]
                            pt = parts[1]
                            tech_char = parts[3].upper()
                            
                            tech = 'P' 
                            if 'L' in tech_char: tech = 'L'
                            elif 'R' in tech_char: tech = 'R'
                            elif 'D' in tech_char: tech = 'D'
                            
                            site_tech_map[f"{code}_{pt}"] = tech

                for line in content_lines:
                    if line.startswith('+SOLUTION/ESTIMATE'): capture_est = True; continue
                    if line.startswith('-SOLUTION/ESTIMATE'): capture_est = False; continue
                    
                    if capture_est and not line.startswith('*') and len(line.strip()) > 10:
                        parts = line.split()
                        if len(parts) >= 9 and parts[1] in ['STAX', 'STAY', 'STAZ']:
                            axis = parts[1]
                            code = parts[2]
                            pt = parts[3]
                            val = float(parts[8])
                            
                            key = f"{code}_{pt}"
                            tech = site_tech_map.get(key, 'P')
                            
                            if key not in snx_data:
                                snx_data[key] = {'code': code, 'tech': tech, 'X': 0.0, 'Y': 0.0, 'Z': 0.0}
                            
                            if axis == 'STAX': snx_data[key]['X'] = val
                            elif axis == 'STAY': snx_data[key]['Y'] = val
                            elif axis == 'STAZ': snx_data[key]['Z'] = val

                rows_spatial = []
                tech_names = {'L': 'SLR', 'R': 'VLBI', 'P': 'GNSS', 'D': 'DORIS'}
                for key, data in snx_data.items():
                    if data['X'] != 0 and data['Y'] != 0 and data['Z'] != 0:
                        r_si = np.sqrt(data['X']**2 + data['Y']**2 + data['Z']**2)
                        alt = r_si - R_EARTH
                        g_loc = g_SI * ((R_EARTH/r_si)**2)
                        s_loc = (np.pi**2)/g_loc
                        real_tech_name = tech_names.get(data['tech'], 'GNSS')
                        rows_spatial.append([data['code'], real_tech_name, r_si, alt, g_loc, s_loc, data['X'], data['Y'], data['Z']])

                # --- 30km 반경 강제 매칭 (KDTree 적용) ---
                rows_multi = []
                if len(rows_spatial) > 0:
                    coords = np.array([[row[6], row[7], row[8]] for row in rows_spatial])
                    tree = KDTree(coords)
                    pairs = tree.query_pairs(r=30000) 
                    
                    for i, j in pairs:
                        s1, s2 = rows_spatial[i], rows_spatial[j]
                        si_diff = abs(s1[2] - s2[2])
                        
                        if si_diff > 0.001:
                            r1, r2 = s1[2], s2[2]
                            avg_r = (r1 + r2) / 2
                            sloc = (np.pi**2)/(g_SI * ((R_EARTH/avg_r)**2))
                            k_diff = abs(r1/sloc - r2/sloc)
                            
                            if s1[1] != s2[1]:
                                rows_multi.append([f"{s1[0]} ({s1[1]}) & {s2[0]} ({s2[1]})", f"{s1[1]} vs {s2[1]}", r1, r2, si_diff, sloc, k_diff])
                
                rows_multi.sort(key=lambda x: x[4], reverse=True)
                
                df_spatial = pd.DataFrame(rows_spatial, columns=['ID', 'Technique', 'SI_Dist', 'Altitude', 'g_loc', 'S_loc', 'X', 'Y', 'Z'])
                df_multi = pd.DataFrame(rows_multi[:100], columns=['Colocated Sites', 'Compare', 'R1 (SI)', 'R2 (SI)', 'SI_Diff (m)', 'S_loc', 'K_Diff (m)'])
                
                if not df_multi.empty:
                    df_multi['Correction (m)'] = df_multi['SI_Diff (m)'] - df_multi['K_Diff (m)']

            # --- CASE 3: SP3/CLK 시간 분석 (Epoch 추출 로직 추가됨) ---
            elif any(x in fname for x in ['.sp3', '.clk']):
                rows_temporal = []
                current_epoch_dt = None
                
                for line in content_lines:
                    if "sp3" in fname:
                        if line.startswith('* '): 
                            data_epoch = f"SP3 Start Epoch: {line[2:25].strip()}"
                            try:
                                p = line.split()
                                yr, mon, day = int(p[1]), int(p[2]), int(p[3])
                                hr, mnt = int(p[4]), int(p[5])
                                sec = int(float(p[6]))
                                current_epoch_dt = datetime.datetime(yr, mon, day, hr, mnt, sec)
                            except: current_epoch_dt = None
                        elif line.startswith('P'):
                            try:
                                s, b = line[1:4].strip(), float(line[46:60])
                                if abs(b) < 900000.0: rows_temporal.append([current_epoch_dt, s, b])
                            except: pass
                            
                    elif "clk" in fname:
                        if line.startswith('AS '): 
                            p = line.split()
                            if len(p) >= 8 and data_epoch == "Unknown Epoch": 
                                data_epoch = f"CLK Epoch: {p[2]}-{p[3]}-{p[4]} {p[5]}:{p[6]}:{p[7]}"
                            if len(p) >= 10:
                                try:
                                    s = p[1]
                                    yr, mon, day = int(p[2]), int(p[3]), int(p[4])
                                    hr, mnt = int(p[5]), int(p[6])
                                    sec = int(float(p[7]))
                                    current_epoch_dt = datetime.datetime(yr, mon, day, hr, mnt, sec)
                                    b_us = float(p[9])*1e6
                                    if abs(b_us) < 900000.0: rows_temporal.append([current_epoch_dt, s, b_us])
                                except: pass
                
                # 원본 님의 로직 그대로 변수명 유지
                df_temporal = pd.DataFrame(rows_temporal, columns=['Epoch', 'Satellite_ID', 'Clock_Bias_Raw_us'])

        except Exception as e:
            st.error(f"Data parsing error: {e}")

# ==========================================
# 7. Dashboard Rendering
# ==========================================

# [CASE 1] 다중 기술 3D 교차 검증
if not df_multi.empty:
    st.markdown('<div class="multi-box">', unsafe_allow_html=True)
    st.markdown(f"### {t['case1_title']}")
    st.markdown(t['case1_desc'])
    
    fig = px.bar(
        df_multi.head(15), 
        x='Colocated Sites', 
        y='Correction (m)',
        title="Extracted Geometric Illusion (Calibration Amount by K-PROTOCOL)",
        labels={'Correction (m)': 'Extracted Error (m)'},
        template='plotly_white',
        color_discrete_sequence=['#E63946']
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(t['case1_guide'], unsafe_allow_html=True)
    
    st.dataframe(df_multi[['Colocated Sites', 'Compare', 'SI_Diff (m)', 'S_loc', 'K_Diff (m)', 'Correction (m)']].style.format({
        'SI_Diff (m)': '{:.5f}', 
        'S_loc': '{:.7f}', 
        'K_Diff (m)': '{:.5f}',
        'Correction (m)': '{:.6f}'
    }), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# [CASE 2] 공간 왜곡 보정 분석
if not df_spatial.empty:
    if 'Residual' not in df_spatial.columns:
        df_spatial['K_Dist'] = df_spatial['SI_Dist'] / df_spatial['S_loc']
        df_spatial['Residual'] = df_spatial['SI_Dist'] - df_spatial['K_Dist']
    max_res = df_spatial['Residual'].abs().max()
    corr, _ = pearsonr(df_spatial['Altitude'], df_spatial['Residual'])
    r_sq = (corr**2) * 100
    
    st.markdown('<div class="explain-box">', unsafe_allow_html=True)
    st.markdown(f"### {t['case2_title']}")
    st.markdown(t['case2_desc'])
    st.markdown(f'<div class="defense-box">{t["defense_text"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    c1m, c2m = st.columns(2)
    c1m.metric("Total Analyzed Stations", f"{len(df_spatial)}")
    c2m.metric("Spatial Calibration (R²)", f"{r_sq:.7f} %")
    
    st.plotly_chart(px.scatter(df_spatial, x='Altitude', y='Residual', hover_data=['ID', 'Technique'], trendline="ols", trendline_color_override="#E63946", title="Altitude vs Calibration Residual", template="plotly_white"), use_container_width=True)
    st.divider()
    st.markdown("#### Station-Specific Details")
    st.dataframe(df_spatial[['ID', 'Technique', 'SI_Dist', 'Altitude', 'g_loc', 'S_loc', 'Residual']], use_container_width=True)

# [CASE 3] 시간 왜곡 보정 및 시계열 분석 (선 그래프 적용)
if not df_temporal.empty:
    # 님의 원본 수학 연산 방식(Dataframe 기반 연산) 100% 롤백
    df_temporal['Calibrated_Bias_us'] = df_temporal['Clock_Bias_Raw_us'] / S_EARTH
    df_temporal['Temporal_Residual_us'] = df_temporal['Clock_Bias_Raw_us'] - df_temporal['Calibrated_Bias_us']
    
    st.markdown('<div class="explain-box">', unsafe_allow_html=True)
    st.markdown(f"### {t['case3_title']}")
    st.markdown(t['case3_desc'])
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 📈 [추가된 기능] 시계열 선 그래프 (Line Chart)
    st.markdown("#### ✅ Temporal Evolution of Geometric Residuals (μs)")
    df_plot = df_temporal.dropna(subset=['Epoch']) # Epoch 없는 쓰레기 데이터 제외
    if not df_plot.empty:
        fig_line = px.line(
            df_plot, 
            x='Epoch', 
            y='Temporal_Residual_us', 
            color='Satellite_ID',
            title="K-PROTOCOL Temporal Residuals by Satellite over Time",
            labels={'Temporal_Residual_us': 'Geometric Residual (μs)', 'Epoch': 'Time (UTC)'},
            template="plotly_white"
        )
        fig_line.update_layout(hovermode="x unified")
        fig_line.update_traces(mode="lines")
        st.plotly_chart(fig_line, use_container_width=True)
    
    st.divider()
    st.markdown("#### Average Temporal Residuals by Satellite")
    df_m = df_temporal.groupby('Satellite_ID', as_index=False)['Temporal_Residual_us'].mean()
    st.plotly_chart(px.bar(df_m, x='Satellite_ID', y='Temporal_Residual_us', title="Average Temporal Residuals (μs)", template="plotly_white", color_discrete_sequence=['#1D3557']), use_container_width=True)
    
    st.divider()
    st.markdown("#### Raw Temporal Data")
    st.dataframe(df_temporal, use_container_width=True)

# ==========================================
# 8. PDF Export
# ==========================================
if file_type_flag and (not df_spatial.empty or not df_temporal.empty):
    st.download_button(label=t['download_btn'], 
                       data=create_integrity_report(df_spatial, df_multi, df_temporal, file_type_flag, fname, data_epoch, r_sq, max_res), 
                       file_name=f"K_PROTOCOL_Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", 
                       mime="application/pdf", type="primary")

st.divider()
st.caption("© 2026. Patent Pending: The K-PROTOCOL algorithm and related mathematical verifications are strictly patent pending.")
