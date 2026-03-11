import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import gzip
from fpdf import FPDF
import io

# 1. K-PROTOCOL 핵심 상수
G_SI, C_SI = 9.80665, 299792458
S_EARTH = (np.pi**2) / G_SI

st.set_page_config(page_title="K-PROTOCOL Analysis Center", layout="wide")

# PDF 생성 함수 (메모리 버퍼 방식 - 에러 해결)
def create_pdf(summary_df, avg_total):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(190, 10, "K-PROTOCOL OFFICIAL ANALYSIS REPORT", 0, 1, 'C')
    pdf.set_font("helvetica", '', 12)
    pdf.ln(10)
    pdf.cell(190, 10, f"Standard S_earth: {S_EARTH:.9f}", 0, 1, 'L')
    pdf.cell(190, 10, f"Total Average Geometric Residual: {avg_total:.6f} us", 0, 1, 'L')
    pdf.ln(10)
    pdf.cell(40, 10, "Sat_ID", 1, 0, 'C')
    pdf.cell(75, 10, "SI Error (Avg)", 1, 0, 'C')
    pdf.cell(75, 10, "K-Residual (Avg)", 1, 1, 'C')
    for _, row in summary_df.head(20).iterrows():
        pdf.cell(40, 10, str(row['Sat_ID']), 1, 0, 'C')
        pdf.cell(75, 10, f"{row['SI_Clock_Error']:.4f}", 1, 0, 'C')
        pdf.cell(75, 10, f"{row['Geometric_Residual']:.6f}", 1, 1, 'C')
    return pdf.output()

st.title("🛰️ K-PROTOCOL Global Analysis Center")
uploaded_file = st.file_uploader("Upload Data File", type=["sp3", "gz", "clk"])

if uploaded_file:
    # 데이터 파싱
    if uploaded_file.name.endswith('.gz'):
        with gzip.open(uploaded_file, 'rt') as f: content = f.read()
    else: content = uploaded_file.getvalue().decode('utf-8')
    
    rows = []
    is_sp3 = ".sp3" in uploaded_file.name.lower()
    for line in content.splitlines():
        if is_sp3 and line.startswith('P'):
            rows.append([line[1:4].strip(), float(line[46:60])])
        elif not is_sp3 and line.startswith('AS'):
            p = line.split()
            if len(p) >= 10: rows.append([p[1], float(p[9])*1e6])
    
    df = pd.DataFrame(rows, columns=['Sat_ID', 'SI_Clock_Error'])
    df['K_Corrected'] = df['SI_Clock_Error'] / S_EARTH
    df['Geometric_Residual'] = df['SI_Clock_Error'] - df['K_Corrected']
    
    # 전수 조사 요약
    summary = df.groupby('Sat_ID').agg({'SI_Clock_Error':'mean', 'Geometric_Residual':'mean'}).reset_index()
    st.subheader("📊 Full Satellite Survey Report")
    st.dataframe(summary, use_container_width=True)
    
    # 위성 선택
    st.divider()
    sel_sat = st.selectbox("🎯 분석할 위성 선택", summary['Sat_ID'].unique())
    sat_data = df[df['Sat_ID'] == sel_sat].copy().reset_index()
    
    if sel_sat.startswith('R'):
        st.warning("⚠️ GLONASS(R) Detected: Applying Smoothing Filter.")
        sat_data['SI_Clock_Error'] = sat_data['SI_Clock_Error'].rolling(window=10).mean()
        sat_data['K_Corrected'] = sat_data['K_Corrected'].rolling(window=10).mean()

    # --- 실시간 수치 변화 패널 (요청 사항) ---
    st.subheader(f"📈 Real-time Correction Metrics: {sel_sat}")
    m1, m2, m3 = st.columns(3)
    latest_si = sat_data['SI_Clock_Error'].iloc[-1]
    latest_k = sat_data['K_Corrected'].iloc[-1]
    latest_res = sat_data['Geometric_Residual'].iloc[-1]
    
    m1.metric("Current SI Error", f"{latest_si:.4f} μs")
    m2.metric("K-Standard Value", f"{latest_k:.4f} μs", delta=f"{(latest_k - latest_si):.4f} μs")
    m3.metric("Remaining Residual", f"{latest_res:.6f} μs")

    # 그래프
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=sat_data['SI_Clock_Error'], name='SI Standard (Red)', line=dict(color='red')))
    fig.add_trace(go.Scatter(y=sat_data['K_Corrected'], name='K-Protocol (Blue)', line=dict(color='blue')))
    fig.update_layout(yaxis_title="Clock Offset (μs)", height=450)
    st.plotly_chart(fig, use_container_width=True)

    # PDF 다운로드 (수정됨)
    st.divider()
    try:
        pdf_report = create_pdf(summary, summary['Geometric_Residual'].mean())
        st.download_button("📄 Download Official PDF Report", pdf_report, "K_Protocol_Analysis.pdf", "application/pdf")
    except Exception as e:
        st.error(f"PDF 생성 오류: {e}")
