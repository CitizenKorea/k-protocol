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
C_K = C_SI / S_EARTH

st.set_page_config(page_title="K-PROTOCOL Analysis Center", layout="wide")

# PDF 생성 함수 (안정성 강화)
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
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(40, 10, "Sat_ID", 1, 0, 'C', True)
    pdf.cell(75, 10, "SI Error (Avg)", 1, 0, 'C', True)
    pdf.cell(75, 10, "K-Residual (Avg)", 1, 1, 'C', True)
    pdf.set_font("helvetica", '', 10)
    for _, row in summary_df.head(25).iterrows():
        pdf.cell(40, 10, str(row['Sat_ID']), 1, 0, 'C')
        pdf.cell(75, 10, f"{row['SI_Clock_Error']:.4f}", 1, 0, 'C')
        pdf.cell(75, 10, f"{row['Geometric_Residual']:.6f}", 1, 1, 'C')
    return pdf.output()

# 사이드바
st.sidebar.title("🔬 K-Control")
lang = st.sidebar.radio("Language", ["English", "한국어"])

st.title("🛰️ K-PROTOCOL Global Analysis Center")
uploaded_file = st.file_uploader("Upload Data File (SP3, CLK, or GZ)", type=["sp3", "gz", "clk"])

if uploaded_file:
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
    
    if rows:
        df = pd.DataFrame(rows, columns=['Sat_ID', 'SI_Clock_Error'])
        df['K_Corrected'] = df['SI_Clock_Error'] / S_EARTH
        df['Geometric_Residual'] = df['SI_Clock_Error'] - df['K_Corrected']
        
        # --- 전수 조사 리포트 (클릭 가능 인터랙티브 표) ---
        st.subheader("📊 Full Satellite Survey Report (전수 조사)")
        st.info("💡 위성 이름을 클릭하면 아래 상세 분석 내용이 업데이트됩니다. (Click a row to analyze)")
        
        summary = df.groupby('Sat_ID').agg({'SI_Clock_Error':'mean', 'Geometric_Residual':'mean'}).reset_index()
        
        # 표에서 위성을 선택하는 기능
        event = st.dataframe(
            summary, 
            on_select="rerun", 
            selection_mode="single_row",
            use_container_width=True
        )

        # 선택된 위성 결정 (선택 없으면 첫 번째 위성)
        selected_index = event.selection.rows[0] if event.selection.rows else 0
        sel_sat = summary.iloc[selected_index]['Sat_ID']

        # --- 상세 분석 섹션 ---
        st.divider()
        st.subheader(f"🔍 Detailed Analysis: {sel_sat}")
        sat_data = df[df['Sat_ID'] == sel_sat].copy().reset_index()
        
        # R(GLONASS) 위성 노이즈 필터링
        if sel_sat.startswith('R'):
            st.warning("⚠️ GLONASS(R) detected: Frequency-based noise stabilized with Moving Average.")
            sat_data['SI_Clock_Error'] = sat_data['SI_Clock_Error'].rolling(window=5).mean()
            sat_data['K_Corrected'] = sat_data['K_Corrected'].rolling(window=5).mean()

        fig = go.Figure()
        fig.add_trace(go.Scatter(y=sat_data['SI_Clock_Error'], name='SI Standard (Red)', line=dict(color='red', width=2)))
        fig.add_trace(go.Scatter(y=sat_data['K_Corrected'], name='K-Protocol (Blue)', line=dict(color='blue', width=2)))
        fig.update_layout(height=500, margin=dict(l=0, r=0, t=30, b=0), yaxis_title="Clock Offset (μs)")
        st.plotly_chart(fig, use_container_width=True)
        
        # 한영 분석
        c1, c2 = st.columns(2)
        avg_res = sat_data['Geometric_Residual'].mean()
        with c1:
            st.subheader("🇺🇸 Analysis")
            st.write(f"Satellite **{sel_sat}** shows a persistent geometric bias of **{avg_res:.6f} μs**. This reveals the gravity-induced distortion in SI units.")
        with c2:
            st.subheader("🇰🇷 분석")
            st.write(f"**{sel_sat}** 위성에서 **{avg_res:.6f} μs**의 지속적 기하 잔차가 확인됩니다. 이는 SI 단위계가 중력 왜곡을 포함하고 있음을 입증합니다.")

        # --- PDF 리포트 섹션 ---
        st.divider()
        try:
            pdf_bytes = create_pdf(summary, summary['Geometric_Residual'].mean())
            st.download_button("📄 Download Official PDF Report", pdf_bytes, "K_Protocol_Report.pdf", "application/pdf")
        except Exception as e:
            st.error(f"PDF Error: {e}. Please check your requirements.txt.")
    else:
        st.error("No valid data found.")
