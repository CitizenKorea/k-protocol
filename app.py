import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import gzip
from fpdf import FPDF
import base64

# 1. K-PROTOCOL 핵심 상수 및 물리 엔진
G_SI = 9.80665
S_EARTH = (np.pi**2) / G_SI
C_SI = 299792458
C_K = C_SI / S_EARTH

st.set_page_config(page_title="K-PROTOCOL Analysis Center", layout="wide")

# 연구소 스타일 CSS 적용
st.markdown("""
    <style>
    .stApp { background-color: #fcfcfc; }
    .report-card { background-color: #ffffff; padding: 25px; border-radius: 15px; border-left: 5px solid #1f77b4; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# 사이드바: 모드 설정 및 언어
st.sidebar.title("🔬 Control Panel")
mode = st.sidebar.selectbox("Analysis Mode / 분석 모드", ["🛰️ Satellite (SP3/CLK)", "📟 Semiconductor (수율 보정)", "🌀 Particle Accelerator (가속기)"])
lang = st.sidebar.radio("🌐 Language", ["English", "한국어"])

# PDF 리포트 생성 함수
def create_pdf(summary_df, avg_total):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, "K-PROTOCOL OFFICIAL ANALYSIS REPORT", 0, 1, 'C')
    pdf.set_font("Arial", '', 12)
    pdf.cell(190, 10, f"S_earth Standard: {S_EARTH:.9f}", 0, 1, 'L')
    pdf.cell(190, 10, f"Total Average Geometric Residual: {avg_total:.6f} us", 0, 1, 'L')
    pdf.ln(10)
    pdf.cell(40, 10, "Sat_ID", 1)
    pdf.cell(70, 10, "SI Error (Avg)", 1)
    pdf.cell(70, 10, "K-Residual (Avg)", 1)
    pdf.ln()
    for i, row in summary_df.head(15).iterrows():
        pdf.cell(40, 10, str(row['Sat_ID']), 1)
        pdf.cell(70, 10, f"{row['SI_Clock_Error']:.4f}", 1)
        pdf.cell(70, 10, f"{row['Geometric_Residual']:.6f}", 1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

# --- 🛰️ 위성 분석 모드 로직 ---
if "Satellite" in mode:
    st.title("🛰️ K-PROTOCOL Global Satellite Analysis Center")
    uploaded_file = st.file_uploader("Upload SP3/GZ or CLK/GZ file", type=["sp3", "gz", "clk"])

    if uploaded_file:
        if uploaded_file.name.endswith('.gz'):
            with gzip.open(uploaded_file, 'rt') as f: content = f.read()
        else: content = uploaded_file.getvalue().decode('utf-8')
        
        # 유니버설 파싱 로직
        rows = []
        lines = content.splitlines()
        is_sp3 = ".sp3" in uploaded_file.name.lower()
        for line in lines:
            if is_sp3 and line.startswith('P'):
                rows.append([line[1:4].strip(), float(line[46:60])])
            elif not is_sp3 and line.startswith('AS'):
                parts = line.split()
                if len(parts) >= 10: rows.append([parts[1], float(parts[9])*1e6])
        
        df = pd.DataFrame(rows, columns=['Sat_ID', 'SI_Clock_Error'])
        df['K_Corrected'] = df['SI_Clock_Error'] / S_EARTH
        df['Geometric_Residual'] = df['SI_Clock_Error'] - df['K_Corrected']

        # 1. 위성 전수 조사 리포트 (Full Survey)
        st.subheader("📊 Full Satellite Survey Report (전수 조사 요약)")
        summary = df.groupby('Sat_ID').agg({'SI_Clock_Error':'mean', 'Geometric_Residual':'mean'}).reset_index()
        st.dataframe(summary.style.highlight_max(axis=0, color='#ffcccc').highlight_min(axis=0, color='#ccffcc'), use_container_width=True)

        # 2. 개별 위성 상세 그래프
        st.divider()
        sel_sat = st.selectbox("Detailed Analysis / 상세 위성 선택", summary['Sat_ID'])
        sat_data = df[df['Sat_ID'] == sel_sat].reset_index()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=sat_data['SI_Clock_Error'], name='SI Standard', line=dict(color='red')))
        fig.add_trace(go.Scatter(y=sat_data['K_Corrected'], name='K-Protocol', line=dict(color='blue')))
        st.plotly_chart(fig, use_container_width=True)

        # 3. PDF 리포트 다운로드
        st.divider()
        avg_total = summary['Geometric_Residual'].mean()
        pdf_data = create_pdf(summary, avg_total)
        st.download_button("📄 Download Official PDF Report (학회 제출용)", pdf_data, "K_Protocol_Report.pdf", "application/pdf")

# --- 📟 반도체/가속기 모드 로직 (확장 섹션) ---
else:
    st.title(f"🏭 K-PROTOCOL {mode} Mode")
    st.info("이 모드에서는 현장의 국소 중력(g) 값을 입력하여 정밀 공정 오차를 제거합니다.")
    g_local = st.number_input("Input Local Gravity (g_local)", value=9.80665, format="%.6f")
    s_loc = (np.pi**2) / g_local
    
    col1, col2 = st.columns(2)
    col1.metric("Local Distortion (S_loc)", f"{s_loc:.9f}")
    col2.metric("Correction Factor", f"{(s_loc-1)*100:.4f}%")
    
    st.write("### 정밀 계측 데이터 보정 시뮬레이션")
    raw_val = st.number_input("Input Raw Measured Value (nm or ps)", value=100.0)
    st.success(f"K-Standard Corrected Value: {raw_val / s_loc:.6f}")
