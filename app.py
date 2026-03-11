import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import gzip
from fpdf import FPDF
import io

# 1. K-PROTOCOL 핵심 물리 상수
G_SI = 9.80665
S_EARTH = (np.pi**2) / G_SI

st.set_page_config(page_title="K-PROTOCOL Analysis Center", layout="wide")

# PDF 생성 함수 (창시자님 요청 4칸 구성 반영)
def create_pdf(summary_df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(190, 10, "K-PROTOCOL NANO-ANALYSIS REPORT", 0, 1, 'C')
    pdf.set_font("helvetica", '', 11)
    pdf.ln(10)
    pdf.cell(190, 8, f"Geometric Standard (S_earth): {S_EARTH:.9f}", 0, 1, 'L')
    pdf.ln(5)
    
    # 테이블 헤더 (4칸 구성 + ID)
    pdf.set_fill_color(220, 230, 241)
    pdf.cell(25, 10, "ID", 1, 0, 'C', True)
    pdf.cell(45, 10, "SI Standard", 1, 0, 'C', True)
    pdf.cell(45, 10, "K-Protocol", 1, 0, 'C', True)
    pdf.cell(35, 10, "Rate (%)", 1, 0, 'C', True)
    pdf.cell(40, 10, "Residual Var", 1, 1, 'C', True)
    
    pdf.set_font("helvetica", '', 10)
    for _, row in summary_df.iterrows():
        pdf.cell(25, 10, str(row['Sat_ID']), 1, 0, 'C')
        pdf.cell(45, 10, f"{row['SI 기준']:.4f}", 1, 0, 'C')
        pdf.cell(45, 10, f"{row['K-Protocol']:.4f}", 1, 0, 'C')
        pdf.cell(35, 10, f"{row['비율']:.4f}", 1, 0, 'C')
        pdf.cell(40, 10, f"{row['남는변수']:.6f}", 1, 1, 'C')
    return bytes(pdf.output())

# 사이드바
with st.sidebar:
    st.title("🔬 Control")
    st.write(f"**S_earth:** `{S_EARTH:.9f}`")

st.title("🛰️ K-PROTOCOL 글로벌 정밀 분석 센터")

uploaded_file = st.file_uploader("파일(SP3, CLK, GZ)을 업로드하세요", type=["sp3", "gz", "clk"])

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
    
    full_df = pd.DataFrame(rows, columns=['Sat_ID', 'SI 기준'])
    
    # --- 창시자님 요청 4대 핵심 지표 계산 ---
    full_df['K-Protocol'] = full_df['SI 기준'] / S_EARTH
    full_df['남는변수'] = full_df['SI 기준'] - full_df['K-Protocol']
    full_df['비율'] = (full_df['남는변수'] / full_df['SI 기준']).abs() * 100

    # 1. 전수 조사 리포트 (4칸 구성)
    st.subheader("📋 SI 프로토콜 전수 조사 요약")
    summary = full_df.groupby('Sat_ID').agg({
        'SI 기준': 'mean',
        'K-Protocol': 'mean',
        '비율': 'mean',
        '남는변수': 'mean'
    }).reset_index()
    
    st.dataframe(summary.style.format({
        'SI 기준': '{:.4f}',
        'K-Protocol': '{:.4f}',
        '비율': '{:.4f}%',
        '남는변수': '{:.9f}'
    }), use_container_width=True)

    # 2. 실시간 나노 메트릭
    st.divider()
    sel_sat = st.selectbox("🎯 분석 위성 선택", summary['Sat_ID'].unique())
    sat_data = full_df[full_df['Sat_ID'] == sel_sat].copy().reset_index()
    
    col1, col2, col3, col4 = st.columns(4)
    last = sat_data.iloc[-1]
    col1.metric("SI 기준", f"{last['SI 기준']:.4f}")
    col2.metric("K-Protocol", f"{last['K-Protocol']:.4f}")
    col3.metric("비율 (%)", f"{last['비율']:.4f}%")
    col4.metric("남는변수", f"{last['남는변수']:.6f}")

    # 3. 보정 그래프
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=sat_data['SI 기준'], name='SI Standard', line=dict(color='red')))
    fig.add_trace(go.Scatter(y=sat_data['K-Protocol'], name='K-Protocol', line=dict(color='blue')))
    fig.update_layout(yaxis_title="Clock Offset (μs)", height=450)
    st.plotly_chart(fig, use_container_width=True)

    # 4. PDF 다운로드
    try:
        pdf_bytes = create_pdf(summary)
        st.download_button("📄 나노 분석 리포트 PDF 다운로드", pdf_bytes, "K_Report.pdf", "application/pdf")
    except Exception as e:
        st.error(f"PDF 오류: {e}")
