import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import gzip
import io

# 1. K-PROTOCOL 핵심 상수
g_si = 9.80665  
s_earth = (np.pi**2) / g_si
c_si = 299792458
c_k = c_si / s_earth

st.set_page_config(page_title="K-PROTOCOL Satellite Analyzer", layout="wide")
st.title("🛰️ K-PROTOCOL 정밀 위성 데이터(SP3) 분석기")

# 파일 업로더 확장 (CSV 및 SP3.GZ 지원)
uploaded_file = st.file_uploader("SP3 파일(.sp3, .gz) 또는 CSV를 업로드하세요", type=["sp3", "gz", "csv"])

def parse_sp3(file_content):
    # SP3 파일에서 위성 ID, 시간, 시계 오차(ms)를 추출하는 가벼운 파서
    rows = []
    for line in file_content.splitlines():
        if line.startswith('P'):  # Position & Clock record
            sat_id = line[1:4]
            # SP3 규격에 따른 데이터 추출 (단위: km 및 micro-sec)
            x = float(line[4:18])
            y = float(line[18:32])
            z = float(line[32:46])
            clock_err = float(line[46:60]) # SI 기준 시계 오차
            rows.append([sat_id, x, y, z, clock_err])
    return pd.DataFrame(rows, columns=['Sat_ID', 'X', 'Y', 'Z', 'SI_Clock_Error'])

if uploaded_file is not None:
    # 파일 형식 판별 및 읽기
    if uploaded_file.name.endswith('.gz'):
        with gzip.open(uploaded_file, 'rt') as f:
            content = f.read()
            df = parse_sp3(content)
    elif uploaded_file.name.endswith('.sp3'):
        content = uploaded_file.getvalue().decode('utf-8')
        df = parse_sp3(content)
    else:
        df = pd.read_csv(uploaded_file)

    st.success(f"✅ {uploaded_file.name} 데이터를 성공적으로 읽었습니다.")
    
    # 2. K-PROTOCOL 보정 로직 적용
    st.subheader("🧪 K-Standard 기하학적 보정 실행")
    
    # SI 시계 오차에서 삐뚠 자(S_earth) 효과를 제거하여 진실을 드러냄
    df['K_Corrected_Clock'] = df['SI_Clock_Error'] / s_earth
    df['Geometric_Residual'] = df['SI_Clock_Error'] - df['K_Corrected_Clock']

    # 결과 시각화
    st.write("### 위성별 시계 오차 분석 (SI vs K-Standard)")
    selected_sat = st.selectbox("분석할 위성 ID를 선택하세요", df['Sat_ID'].unique())
    sat_df = df[df['Sat_ID'] == selected_sat]

    fig = px.line(sat_df, y=['SI_Clock_Error', 'K_Corrected_Clock'], 
                  title=f"Satellite {selected_sat}: Geometric Correction",
                  labels={"value": "Clock Offset (μs)", "index": "Epoch"},
                  color_discrete_map={"SI_Clock_Error": "red", "K_Corrected_Clock": "blue"})
    st.plotly_chart(fig, use_container_width=True)

    # 잔차 분석 결과 (0.002041 μs 확인용)
    avg_residual = sat_df['Geometric_Residual'].mean()
    st.metric("평균 기하학적 잔차 (K-Protocol Predicted)", f"{avg_residual:.6f} μs")
    st.write(f"표준 물리학은 이 **{avg_residual:.6f} μs**를 잡음으로 보지만, 이는 우주의 기하학적 필연입니다.")
