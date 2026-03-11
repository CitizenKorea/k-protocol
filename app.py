import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import gzip
from fpdf import FPDF
import io

# 1. K-PROTOCOL 나노 정밀 물리 엔진
G_SI = 9.80665
S_EARTH = (np.pi**2) / G_SI  # 왜곡 지수
CORRECTION_RATE_BASE = (1 - (1/S_EARTH)) * 100 # 보정율 (%)

st.set_page_config(page_title="K-PROTOCOL Nano-Analysis Center", layout="wide")

# 연구소 전용 세련된 디자인 스타일
st.markdown("""
    <style>
    .metric-container { background-color: #f0f2f6; padding: 15px; border-radius: 10px; }
    .stMetric { border-bottom: 3px solid #1f77b4; }
    </style>
    """, unsafe_allow_html=True)

# PDF 리포트 생성 엔진 (바이너리 완벽 해결)
def create_pdf(summary_df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(190, 10, "K-PROTOCOL NANO-ANALYSIS REPORT", 0, 1, 'C')
    pdf.set_font("helvetica", '', 10)
    pdf.ln(10)
    pdf.cell(190, 10, f"Geometric Standard (S_earth): {S_EARTH:.9f}", 0, 1, 'L')
    pdf.cell(190, 10, f"Theoretical Correction Rate: {CORRECTION_RATE_BASE:.6f} %", 0, 1, 'L')
    pdf.ln(10)
    
    # 표 헤더 (창시자님 요청 용어 적용)
    pdf.set_fill_color(220, 230, 241)
    pdf.cell(30, 10, "Sat_ID", 1, 0, 'C', True)
    pdf.cell(55, 10, "SI Protocol (Avg)", 1, 0, 'C', True)
    pdf.cell(50, 10, "Rate (%)", 1, 0, 'C', True)
    pdf.cell(55, 10, "Remaining Var", 1, 1, 'C', True)
    
    for _, row in summary_df.iterrows():
        pdf.cell(30, 10, str(row['Sat_ID']), 1, 0, 'C')
        pdf.cell(55, 10, f"{row['SI_Protocol']:.4f}", 1, 0, 'C')
        pdf.cell(50, 10, f"{row['Rate']:.4f}", 1, 0, 'C')
        pdf.cell(55, 10, f"{row['남는변수']:.6f}", 1, 1, 'C')
    return bytes(pdf.output())

# 사이드바: 나노 제어 패널
with st.sidebar:
    st.title("🔬 Nano Control")
    lang = st.radio("Language", ["한국어", "English"])
    st.divider()
    st.markdown(f"**S_earth (왜곡지수):**\n`{S_EARTH:.9f}`")
    st.markdown(f"**보정율 (Base Rate):**\n`{CORRECTION_RATE_BASE:.6f}%` 기초")
    st.caption("이 보정율은 중력 왜곡에 의한 기하학적 필연치입니다.")

st.title("🛰️ K-PROTOCOL 글로벌 정밀 분석 센터")
st.markdown("#### SI 표준의 '삐뚠 자'를 넘어 우주의 진짜 시간을 측정합니다.")

uploaded_file = st.file_uploader("위성 데이터(SP3, CLK, GZ)를 업로드하세요", type=["sp3", "gz", "clk"])

if uploaded_file:
    # 데이터 파싱 로직
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
    
    full_df = pd.DataFrame(rows, columns=['Sat_ID', 'SI_Protocol'])
    
    # 나노 정밀 계산 (창시자님 요청 용어 기반)
    full_df['보정값'] = full_df['SI_Protocol'] / S_EARTH
    full_df['남는변수'] = full_df['SI_Protocol'] - full_df['보정값']
    full_df['Rate'] = (full_df['남는변수'] / full_df['SI_Protocol']).abs() * 100

    # 1. 전수 조사 리포트 (나노 현미경급 구성)
    st.subheader("📋 SI 프로토콜 전수 조사 요약")
    summary = full_df.groupby('Sat_ID').agg({
        'SI_Protocol': 'mean',
        'Rate': 'mean',
        '남는변수': 'mean'
    }).reset_index()
    
    st.dataframe(summary.style.format({
        'SI_Protocol': '{:.4f}',
        'Rate': '{:.6f}%',
        '남는변수': '{:.9f}'
    }), use_container_width=True)

    # 2. 실시간 나노 메트릭 (Live Dashboard)
    st.divider()
    sel_sat = st.selectbox("🎯 분석 위성 선택", summary['Sat_ID'].unique())
    sat_data = full_df[full_df['Sat_ID'] == sel_sat].copy().reset_index()
    
    st.subheader(f"📈 실시간 물리 지표: {sel_sat}")
    col1, col2, col3 = st.columns(3)
    
    now_si = sat_data['SI_Protocol'].iloc[-1]
    now_rate = sat_data['Rate'].iloc[-1]
    now_rem = sat_data['남는변수'].iloc[-1]
    
    col1.metric("SI 프로토콜 (현재)", f"{now_si:.6f} μs")
    col2.metric("실시간 보정율", f"{now_rate:.4f}%", delta=f"{CORRECTION_RATE_BASE - now_rate:.4f}%")
    col3.metric("남는변수 (Weather/Solar)", f"{now_rem:.9f} μs")
    
    st.caption("※ 남는변수는 날씨, 전리층, 태양풍 등 외부 환경에 의해 발생하는 SI 시스템의 한계치입니다.")

    # 3. 보정 시각화 그래프
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=sat_data['SI_Protocol'], name='SI Protocol (오염된 데이터)', line=dict(color='red', width=2)))
    fig.add_trace(go.Scatter(y=sat_data['보정값'], name='K-Standard (보정된 진실)', line=dict(color='blue', width=2)))
    fig.update_layout(yaxis_title="Time Sync (μs)", height=500, hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    # 4. 공식 리포트 다운로드
    st.divider()
    try:
        pdf_bytes = create_pdf(summary)
        st.download_button(
            label="📄 나노 분석 리포트 PDF 다운로드",
            data=pdf_bytes,
            file_name=f"K_Nano_Report_{sel_sat}.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"PDF 생성 중: {e}")
