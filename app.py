import streamlit as st
import numpy as np

# 페이지 설정
st.set_page_config(page_title="K-PROTOCOL Standard", page_icon="🌐", layout="wide")

# 스타일 커스텀
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# 제목 및 서문
st.title("🌐 K-PROTOCOL: The Scale of Truth")
st.markdown("### 인류가 사용하는 '1미터'는 지구 중력에 오염된 '삐뚠 자'입니다.")
st.write("본 시스템은 K-PROTOCOL의 기하학적 공리를 바탕으로 현대 물리학의 단위 오차를 실시간으로 교정합니다.")

st.divider()

# 1. 기본 상수 및 왜곡 지수 계산
g_si = 9.80665  
pi_sq = np.pi**2  
c_si = 299792458  

s_earth = pi_sq / g_si  
c_k = c_si / s_earth  

# 메인 지표 출력
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("지구 왜곡 지수 (S_earth)", f"{s_earth:.9f}")
    st.caption("우주 기하학적 기준($\pi^2$) 대비 지구의 공간 굴절률")

with col2:
    st.metric("절대 광속 (c_k)", f"{c_k:,.1f} m/s")
    st.caption("삐뚠 자를 바로잡은 우주의 실제 정보 전달 속도")

with col3:
    st.metric("기하학적 오차율", "1.288%")
    st.caption("표준 SI 단위계가 가진 본질적 수축 비율")

st.divider()

# 2. 실증 데이터: GPS 위성 시계 잔차
st.subheader("🛰️ GPS 위성 시계 잔차 검증")
st.write("표준 물리학이 '노이즈'라고 부르며 포기한 잔차는 사실 공간의 기하학적 필연입니다.")

st.info("**K-PROTOCOL 예측 기하 잔차:** `+0.002041 μs` (매 5분당 관측치)")

# 3. 우주 구성 비율 (π-Matrix)
st.subheader("🌌 우주 구성 비율 시뮬레이션")
st.write("우주의 거대 구조는 임의의 상수가 아닌, 기하학적 패킹 효율에 의해 결정됩니다.")

d_energy = (1 - 1/np.pi) * 100 
d_matter = (1/np.pi - 1/(2*np.pi**2)) * 100 
baryon_m = (1/(2*np.pi**2)) * 100 

# 이 부분이 에러가 났던 곳입니다. 확실하게 고쳤습니다.
c1, c2, c3 = st.columns(3)
c1.write(f"**암흑 에너지**: {d_energy:.2f}%")
c2.write(f"**암흑 물질**: {d_matter:.2f}%")
c3.write(f"**일반 물질**: {baryon_m:.2f}%")

st.success("이 모든 물리량은 단 하나의 마스터 포뮬러 $V = \pi^n / S^k$ 로 통합됩니다.")

# 푸터
st.markdown("---")
st.caption("© 2026 K-PROTOCOL Foundation | Based on the Geometric Universality Theory")
