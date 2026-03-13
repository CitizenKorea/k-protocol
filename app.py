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
st.set_page_config(page_title="K-PROTOCOL Analysis Center", layout="wide", page_icon="🛰️")

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
* **지구 절대 척도 ($S_{earth}$)**: $\frac{\pi^2}{g_{si}} = \frac{\pi^2}{9.80665} \approx 1.006494$
* **K-보정 광속 ($c_k$)**: $\frac{c_{si}}{S_{earth}} = \frac{299,792,458}{1.006494...} \approx 297,858,458.1 \text{ m/s}$

나아가, 각 지점의 고도($h$)와 지구 반경($R$)에 따른 **국소 중력($g_{loc}$)**을 반영하여 개별 척도 계수($S_{loc}$)를 산출함으로써 가장 정밀하고 진실된 물리 값을 도출합니다.
* **국소 중력 ($g_{loc}$)**: $g_{si} \times \left(\frac{R_{earth}}{R_{earth} + h}\right)^2$
* **국소 척도 계수 ($S_{loc}$)**: $\frac{\pi^2}{g_{loc}}$

상세한 수학적 근거와 이론적 배경은 아래 **Zenodo 링크**를 통해 확인하실 수 있습니다. 당신의 데이터를 업로드하여 기존 표준 속에 숨겨진 진실을 직접 목격하십시오.
        """,
        'upload_prompt': "SNX, SP3, CLK 파일을 드래그 앤 드롭 하십시오",
        'insight_msg': "이 수치는 수학적 사실입니다. 정답은 오직 데이터 속에 있습니다.",
    },
    'ENG': {
        'title': "K-PROTOCOL Open Analysis Center",
        'subtitle': "Let the data speak. Judge for yourself.",
        'bg_title': "⚖️ Why Do Errors Occur? (Circular Logic and Limitations of SI Units)",
        'bg_text': r"""
The persistent errors found in modern precision data arise from the **'circular logic of the conventional SI unit system.'** A system that defines distance by the speed of light, and then measures light by that same distance, is fundamentally incapable of calibrating the geometric distortions of spacetime.

K-PROTOCOL breaks this cycle utilizing the universal geometric constant $S_{earth}$ and the calibrated speed of light $c_k$.
* **Earth Absolute Metric ($S_{earth}$)**: $\frac{\pi^2}{g_{si}} = \frac{\pi^2}{9.80665} \approx 1.006494$
* **Calibrated Speed of Light ($c_k$)**: $\frac{c_{si}}{S_{earth}} = \frac{299,792,458}{1.006494...} \approx 297,858,458.1 \text{ m/s}$

Furthermore, by accounting for the **local gravity ($g_{loc}$)** at each point and altitude ($h$) to derive the specific metric factor ($S_{loc}$), it reveals the most precise and authentic physical values.
* **Local Gravity ($g_{loc}$)**: $g_{si} \times \left(\frac{R_{earth}}{R_{earth} + h}\right)^2$
* **Local Metric Factor ($S_{loc}$)**: $\frac{\pi^2}{g_{loc}}$

For detailed mathematical evidence and theoretical background, please refer to the **Zenodo Link** below. Upload your data to witness the truth hidden beneath conventional standards.
        """,
        'upload_prompt': "Drag and drop SNX, SP3, or CLK files",
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
    st.markdown("<div class='link-box'>📡 <a href='http://garner.ucsd.edu/pub/products/2392/' target='_blank'>Raw Data Directory for Verification</a></div>", unsafe_allow_html=True)

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
    pdf.cell(190, 8, f"Author: CK (CitizenKorea)", 0, 1, 'L')
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

    pdf.ln(15); pdf.set_font("helvetica", 'I', 9)
    pdf.multi_cell(190, 6, "Notice: All calculation results are mathematically derived directly from the uploaded raw data without any manipulation. The truth lies within the data.")
    out = pdf.output(dest='S')
    return out.encode('latin-1') if isinstance(out, str) else bytes(out)

# ==========================================
# 7. Dynamic Analysis Engine
# ==========================================
uploaded_file = st.file_uploader(t['upload_prompt'], type=["snx", "sp3", "clk", "gz"])

if uploaded_file:
    fname = uploaded_file.name.lower()
    df = pd.DataFrame()
    file_type_flag = None; r_sq = None; max_res = None
    data_epoch = "Time/Epoch data not explicitly found in header"
    
    with st.spinner("Analyzing data integrity & Extracting Data Epoch..."):
        # --- SNX Parser ---
        if ".snx" in fname:
            file_type_flag = 'SNX'
            snx_data = {}
            f = gzip.open(uploaded_file, 'rt') if fname.endswith('.gz') else io.TextIOWrapper(uploaded_file)
            capture = False
            for line in f:
                if line.startswith('%=SNX'):
                    data_epoch = f"SNX Base Header [{line.strip()[:50]}]"
                
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
                df['K_Dist'] = df['SI_Dist'] / df['S_loc']; df['Residual'] = df['SI_Dist'] - df['K_Dist']
                max_res = df['Residual'].abs().max()
                corr, _ = pearsonr(df['Altitude'], df['Residual']); r_sq = (corr**2) * 100
                st.subheader("Spatial Metric Calibration Results (SNX)")
                
                # 1. 고도 vs 잔차 산점도
                st.plotly_chart(px.scatter(df, x='Altitude', y='Residual', hover_data=['ID'], trendline="ols", trendline_color_override="#0056B3", title=f"Actual Correlation (Altitude vs Residual) | R² = {r_sq:.7f}%", template="plotly_white"), use_container_width=True)
                st.divider()

                # 2. 관측소 고도 순서 기반 이중 선형 그래프 추가
                st.markdown("#### Detailed Analysis: SI Standard vs K-PROTOCOL (Spatial Distance)")
                df_sorted = df.sort_values(by='Altitude').reset_index(drop=True)
                fig_snx_line = px.line(df_sorted, x='ID', y=['SI_Dist', 'K_Dist'], 
                                       title="Spatial Distance Comparison across Stations (Sorted by Altitude)",
                                       labels={'ID': 'Station ID (Sorted by Altitude)', 'value': 'Distance (m)', 'variable': 'Standard'},
                                       template="plotly_white",
                                       color_discrete_map={'SI_Dist': '#6C757D', 'K_Dist': '#E63946'},
                                       hover_data={'Altitude': True})
                newnames_snx = {'SI_Dist': 'SI Standard (Raw)', 'K_Dist': 'K-PROTOCOL (Calibrated)'}
                fig_snx_line.for_each_trace(lambda t: t.update(name = newnames_snx[t.name], legendgroup = newnames_snx[t.name], hovertemplate = t.hovertemplate.replace(t.name, newnames_snx[t.name])))
                fig_snx_line.update_traces(mode='lines+markers')
                st.plotly_chart(fig_snx_line, use_container_width=True)

                st.divider()
                st.markdown("#### Station-Specific Details")
                sel_station = st.selectbox("Select Station ID:", df['ID'].unique())
                df_s = df[df['ID'] == sel_station].iloc[0]
                c1m, c2m, c3m = st.columns(3)
                c1m.metric("Local Gravity (g_loc)", f"{df_s['g_loc']:.6f}"); c2m.metric("Metric (S_loc)", f"{df_s['S_loc']:.7f}"); c3m.metric("Residual (m)", f"{df_s['Residual']:,.2f}")
                st.dataframe(df, use_container_width=True)

        # --- SP3/CLK Parser ---
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
                st.dataframe(df, use_container_width=True)

    # ==========================================
    # 8. Export & Verification (Data Epoch 추가 전달)
    # ==========================================
    if not df.empty and file_type_flag:
        st.info(f"💡 {t['insight_msg']}")
        st.download_button(label="📄 Download Analytical Integrity Report (PDF)", 
                           data=create_integrity_report(df, file_type_flag, uploaded_file.name, data_epoch, r_sq, max_res), 
                           file_name=f"K_PROTOCOL_Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", 
                           mime="application/pdf", type="primary")

# ==========================================
# 9. Footer (인용구 강화)
# ==========================================
st.divider()
c_foot1, c_foot2 = st.columns([2, 1])

with c_foot1:
    st.markdown("**📝 Citation (논문 인용)**")
    st.code("CK (CitizenKorea). (2026). K-PROTOCOL: Grand Unification via Sloc. Zenodo. https://doi.org/10.5281/zenodo.18976813", language="text")

with c_foot2:
    st.markdown("**🤝 Collaboration & Inquiries**")
    st.markdown("Email: [estake@naver.com](mailto:estake@naver.com)")
    st.markdown("Author: CK (CitizenKorea)")

st.caption("© 2026. Patent Pending: The K-PROTOCOL algorithm and related mathematical verifications are strictly patent pending.")
