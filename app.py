import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px

# 페이지 설정
st.set_page_config(page_title="K-PROTOCOL Analysis Center", layout="wide")

# 1. K-PROTOCOL 핵심 엔진 상수
g_si = 9.80665  
s_earth = (np.pi**2) / g_si
c_si = 299792458
c_k = c_si / s_earth

st.title("🛰️ K-PROTOCOL 실전 데이터 분석 센터")
st.write("표준 단위계의 '삐뚠 자'로 인해 발생한 데이터 왜곡을 실시간으로 교정합니다.")

# 사이드바: 이론 요약
st.sidebar.header("K-PROTOCOL Axioms")
st.sidebar.write(f"**S_earth:** {s_earth:.9f}")
st.sidebar.write(f"**Absolute c_k:** {c_k:,.2f} m/s")

# 2. 데이터 업로드 섹션
st.divider()
st.subheader("📁 검증 데이터 업로드")
uploaded_file = st.file_uploader("GPS 잔차 또는 반도체 계측 데이터(CSV)를 선택하세요", type=["csv"])

if uploaded_file is not None:
    # 데이터 읽기
    df = pd.read_csv(uploaded_file)
    st.write("✅ 원본 데이터 미리보기:")
    st.dataframe(df.head())

    # 분석할 컬럼 선택 (예: 'error' 또는 'residual' 컬럼이 있다고 가정)
    col_to_fix = st.selectbox("보정할 오차 컬럼을 선택하세요", df.columns)

    if st.button("K-Standard 보정 실행"):
        # 보정 로직: 삐뚠 자 효과(1.288%)를 제거하는 수식 적용
        df['Corrected_Data'] = df[col_to_fix] / s_earth
        
        # 결과 시각화
        st.subheader("📊 보정 결과 비교")
        fig = px.line(df, y=[col_to_fix, 'Corrected_Data'], 
                      title="Original (Red) vs K-Standard Corrected (Blue)",
                      labels={"value": "Error Value", "index": "Time/Point"},
                      color_discrete_map={col_to_fix: "red", "Corrected_Data": "blue"})
        st.plotly_chart(fig, use_container_width=True)
        
        st.success(f"축사합니다! {col_to_fix}의 기하학적 왜곡이 제거되었습니다.")
        st.download_button("보정된 데이터 다운로드", df.to_csv(index=False), "corrected_data.csv")

else:
    st.info("분석할 CSV 파일을 업로드해 주세요. (컬럼명에 '오차' 혹은 '잔차' 수치가 포함되어야 합니다.)")
    
    # 테스트용 샘플 데이터 생성 버튼
    if st.sidebar.button("테스트용 샘플 데이터 생성"):
        test_df = pd.DataFrame({
            'Time': np.arange(0, 100),
            'GPS_Residual': np.random.normal(0.002041, 0.0001, 100) # 문서 속 0.002041 반영
        })
        st.sidebar.download_button("샘플 CSV 받기", test_df.to_csv(index=False), "sample.csv")
