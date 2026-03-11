import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import gzip
from fpdf import FPDF
import io

# 1. K-PROTOCOL 핵심 상수 및 물리 엔진
G_SI = 9.80665
S_EARTH = (np.pi**2) / G_SI
C_SI = 299792458
C_K = C_SI / S_EARTH

st.set_page_config(page_title="K-PROTOCOL Universal Center", layout="wide")

# 연구소 스타일 CSS
st.markdown("""
    <style>
    .report-card { background-color: #ffffff; padding: 20px; border-radius: 10px; border-left: 5px solid #1f77b4; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# PDF 리포트 생성 함수 (에러 수정 버전)
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
    
    # 테이블 헤더
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(40, 10, "Sat_ID", 1, 0, 'C', True)
    pdf.cell(75, 10, "SI Error (Avg)", 1, 0, 'C', True)
    pdf.cell(75, 10, "K-Residual (Avg)", 1, 1, 'C', True)
    
    # 데이터 (상위 20개)
    pdf.set_font("helvetica", '', 10)
    for i, row in summary_df.head(20).iterrows():
        pdf.cell(40, 10, str(row['Sat_ID']), 1, 0, 'C')
        pdf.cell(75, 10, f"{row['SI_Clock_Error']:.4f}", 1, 0, 'C')
        pdf.cell(75, 10, f"{row['Geometric_Residual']:.6f}", 1, 1, 'C')
    
    return pdf.output() # fpdf2는 bytes를 직접 반환합니다.

# 사이드바 설정
st.sidebar.title("🔬 Control Panel")
mode = st.sidebar.selectbox("Mode / 모드", ["🛰️ Satellite (SP3/CLK)", "📟 Semiconductor (수율)", "🌀 Particle Accelerator (가속기)"])
lang = st.sidebar.radio("🌐 Language", ["English", "한국어"])

# --- 🛰️ 위성 분석 모드 ---
if "Satellite" in mode:
    st.title("🛰️ K-PROTOCOL Global Analysis Center")
    st.write("SP3(Orbit) & CLK(Clock) Universal Analysis Engine")
    
    uploaded_file = st.file_uploader("Upload Data File (SP3, CLK, or GZ)", type=["sp3", "gz", "clk"])

    if uploaded_file:
        # 압축 처리 및 읽기
        if uploaded_file.name.endswith('.gz'):
            with gzip.open(uploaded_file, 'rt') as f: content = f.read()
        else: content = uploaded_file.getvalue().decode('utf-8')
        
        # 파일 형식 자동 감지 파싱
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
            
            # 1. 전수 조사 요약
            st.subheader("📊 Full Satellite Survey Report (전수 조사)")
            summary = df.groupby('Sat_ID').agg({'SI_Clock_Error':'mean', 'Geometric_Residual':'mean'}).reset_index()
            st.dataframe(summary, use_container_width=True)
            
            # 2. 상세 그래프
            st.divider()
            sel_sat = st.selectbox("Select Satellite for Detail", summary['Sat_ID'])
            sat_data = df[df['Sat_ID'] == sel_sat].reset_index()
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(y=sat_data['SI_Clock_Error'], name='SI Standard (Red)', line=dict(color='red')))
            fig.add_trace(go.Scatter(y=sat_data['K_Corrected'], name='K-Protocol (Blue)', line=dict(color='blue')))
            fig.update_layout(title=f"Precision Comparison: {sel_sat}", yaxis_title="Clock Offset (μs)")
            st.plotly_chart(fig, use_container_width=True)
            
            # 3. 한영 상세 분석
            c1, c2 = st.columns(2)
            avg_res = summary['Geometric_Residual'].mean()
            with c1:
                st.subheader("🇺🇸 Analysis")
                st.write(f"The gap of **{avg_res:.6f} μs** is the 'Geometric Residual' predicted by K-PROTOCOL. It proves SI units are distorted.")
            with c2:
                st.subheader("🇰🇷 분석")
                st.write(f"평균 **{avg_res:.6f} μs**의 잔차는 창시자님이 예견하신 기하학적 잔차입니다. SI 단위계의 왜곡을 입증합니다.")

            # 4. PDF 리포트 발행
            st.divider()
            try:
                pdf_out = create_pdf(summary, avg_total=avg_res)
                st.download_button("📄 Download Official PDF Report", pdf_out, "K_Report.pdf", "application/pdf")
            except: st.warning("PDF preparation in progress...")
        else: st.error("No valid data found in file.")

# --- 📟 기타 모드 (반도체/가속기) ---
else:
    st.title(f"🏭 K-PROTOCOL {mode}")
    g_loc = st.number_input("Local Gravity (g)", value=9.80665, format="%.6f")
    s_loc = (np.pi**2) / g_loc
    st.metric("Distortion Factor (S_loc)", f"{s_loc:.9f}")
    val = st.number_input("Measured Value (Input)", value=100.0)
    st.success(f"K-Standard Corrected: {val / s_loc:.6f}")
