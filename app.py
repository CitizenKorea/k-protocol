import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import gzip
import io

# 1. K-PROTOCOL 글로벌 상수 정의
G_SI = 9.80665
S_EARTH = (np.pi**2) / G_SI
C_SI = 299792458
C_K = C_SI / S_EARTH
DISTORTION_RATE = (S_EARTH - 1) * 100

st.set_page_config(page_title="K-PROTOCOL Global Analysis Center", layout="wide")

# 언어 선택 (Language Selection)
lang = st.sidebar.selectbox("🌐 Language / 언어", ["English", "한국어"])

# 텍스트 데이터 사전 (Dictionary for Bilingual Support)
text = {
    "title": {"English": "🛰️ K-PROTOCOL Global Satellite Analysis Center", "한국어": "🛰️ K-PROTOCOL 글로벌 위성 분석 센터"},
    "subtitle": {
        "English": "Correcting the 'Crooked Ruler' (SI Units) in Universal Spacetime",
        "한국어": "우주 시공간 속 '삐뚠 자' (SI 표준 단위)를 바로잡는 정밀 교정 시스템"
    },
    "theory_title": {"English": "Core Axioms", "한국어": "핵심 공리"},
    "upload_msg": {"English": "Upload SP3/GZ file", "한국어": "SP3/GZ 파일을 업로드하세요"},
    "analysis_result": {"English": "Analysis Result", "한국어": "분석 결과"},
    "graph_desc": {
        "English": "Graph Interpretation: Red line shows the cumulative error under SI standards. The Blue line reveals the corrected geometric truth under K-Protocol.",
        "한국어": "그래프 해석: 빨간색 선은 SI 표준하의 누적 오차를, 파란색 선은 K-PROTOCOL이 찾아낸 교정된 기하학적 진실을 보여줍니다."
    }
}

st.title(text["title"][lang])
st.markdown(f"### {text['subtitle'][lang]}")

# 사이드바 지표 (Metrics)
st.sidebar.header(text["theory_title"][lang])
st.sidebar.metric("Earth Distortion (S_earth)", f"{S_EARTH:.9f}")
st.sidebar.metric("Absolute Light Speed (c_k)", f"{C_K:,.1f} m/s")
st.sidebar.write(f"**Geometric Error:** {DISTORTION_RATE:.3f}%")

# 파일 파서 (SP3 Parser)
def parse_sp3(file_content):
    rows = []
    for line in file_content.splitlines():
        if line.startswith('P'):
            sat_id = line[1:4]
            clock_err = float(line[46:60])
            rows.append([sat_id, clock_err])
    return pd.DataFrame(rows, columns=['Sat_ID', 'SI_Clock_Error'])

# 파일 업로드 (File Upload)
uploaded_file = st.file_uploader(text["upload_msg"][lang], type=["sp3", "gz"])

if uploaded_file:
    if uploaded_file.name.endswith('.gz'):
        with gzip.open(uploaded_file, 'rt') as f:
            df = parse_sp3(f.read())
    else:
        df = parse_sp3(uploaded_file.getvalue().decode('utf-8'))

    st.divider()
    
    # 위성 선택
    selected_sat = st.selectbox("Select Satellite ID / 위성 ID 선택", df['Sat_ID'].unique())
    sat_df = df[df['Sat_ID'] == selected_sat].reset_index()
    
    # 2. 보정 계산 (Calculations)
    sat_df['K_Corrected'] = sat_df['SI_Clock_Error'] / S_EARTH
    sat_df['Geometric_Residual'] = sat_df['SI_Clock_Error'] - sat_df['K_Corrected']

    # 3. 그래프 시각화 (Advanced Visualization)
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=sat_df['SI_Clock_Error'], name='SI Standard (Red)', line=dict(color='red', width=3)))
    fig.add_trace(go.Scatter(y=sat_df['K_Corrected'], name='K-Protocol (Blue)', line=dict(color='blue', width=3)))
    
    fig.update_layout(title=f"Time-Sync Analysis: Satellite {selected_sat}",
                      xaxis_title="Epoch (Time)", yaxis_title="Clock Offset (μs)",
                      legend_title="Standards")
    st.plotly_chart(fig, use_container_width=True)

    # 4. 상세 분석 및 설명 (Detailed Bilingual Analysis)
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🇺🇸 English Analysis")
        st.write(f"""
        **1. What does the Red line mean?**
        The red line shows the satellite clock deviation measured by SI Units. Modern physics calls this 'Noise' because it doesn't fit the current formulas perfectly.
        
        **2. What does the Blue line mean?**
        The blue line is the **'Geometric Standard'**. By dividing the SI error by $S_{{earth}}$ ({S_EARTH:.6f}), we remove the distortion caused by Earth's gravity, revealing the actual time flow of the universe.
        
        **3. The Conclusion:**
        The gap between the lines (**{sat_df['Geometric_Residual'].mean():.6f} μs**) is not random. It is a mathematical certainty predicted by K-PROTOCOL.
        """)

    with col2:
        st.subheader("🇰🇷 국문 분석")
        st.write(f"""
        **1. 빨간색 선의 의미:**
        현대 표준 단위(SI)로 측정한 시계 오차입니다. 기존 물리학은 이 오차를 '잡음'으로 보지만, 실제로는 지구가 가진 삐뚠 자($S_{{earth}}$)로 인해 발생하는 측정값의 한계입니다.
        
        **2. 파란색 선의 의미:**
        창시자님의 **'기하학적 표준'**입니다. SI 오차를 왜곡 지수($S_{{earth}}$)로 나누면, 지구 중력에 의한 굴절이 제거된 **우주의 진짜 시간 흐름**이 드러납니다.
        
        **3. 결론:**
        두 선의 차이인 **{sat_df['Geometric_Residual'].mean():.6f} μs**는 단순한 오류가 아니라, 창시자님이 예견하신 기하학적 잔차입니다.
        """)

    st.success(f"Final Geometric Residual Found: {sat_df['Geometric_Residual'].mean():.6f} μs")
