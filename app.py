import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from scipy.stats import pearsonr

# ==========================================
# 1. K-PROTOCOL Constants
# ==========================================
G_SI = 9.80665
R_EARTH = 6371000
S_EARTH = (np.pi**2) / G_SI 

st.set_page_config(page_title="K-PROTOCOL Omni Analysis Center", layout="wide", page_icon="🛰️")

st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; color: #212529; }
    .metric-box { background-color: #FFFFFF; padding: 20px; border-left: 4px solid #0056B3; border-radius: 5px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .metric-value { font-size: 24px; font-weight: 700; color: #212529; }
    .multi-box { border: 3px solid #E63946; padding: 25px; border-radius: 10px; background-color: #fff0f0; margin-bottom: 30px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛰️ K-PROTOCOL Omni Analysis Center")
st.markdown("#### The Absolute Proof: ITRF2020 Spatial Metric Calibration")

# ==========================================
# 2. 3D Proximity Parsing Engine
# ==========================================
uploaded_file = st.file_uploader("추출된 .snx 파일을 업로드하세요 (K_PROTOCOL_EVIDENCE.snx)", type=["snx"])

if uploaded_file:
    with st.spinner("3D 공간 근접 교차 검증 및 K-PROTOCOL 분석 중..."):
        site_tech_map = {}
        snx_data = {}
        capture_site, capture_est = False, False
        
        # 파일 한 줄씩 정밀 파싱
        content = uploaded_file.read().decode('utf-8', errors='ignore').splitlines()
        
        for line in content:
            if line.startswith('+SITE/ID'): capture_site = True; continue
            if line.startswith('-SITE/ID'): capture_site = False; continue
            if capture_site and not line.startswith('*') and len(line) >= 20:
                code = line[1:5].strip()
                # 빈칸 이동에 흔들리지 않는 기술 식별 (18번, 19번 인덱스 동시 확인)
                c19 = line[19:20].upper()
                c18 = line[18:19].upper()
                if c19 in ['P', 'L', 'R', 'D']: tech = c19
                elif c18 in ['P', 'L', 'R', 'D']: tech = c18
                else: tech = 'P'
                site_tech_map[code] = tech

            if line.startswith('+SOLUTION/ESTIMATE'): capture_est = True; continue
            if line.startswith('-SOLUTION/ESTIMATE'): capture_est = False; continue
            if capture_est and not line.startswith('*'):
                p = line.split()
                # STAX, STAY, STAZ 3차원 좌표 확보
                if len(p) >= 9 and p[1] in ['STAX', 'STAY', 'STAZ']:
                    axis, code, val = p[1], p[2], float(p[8])
                    tech = site_tech_map.get(code, 'P')
                    
                    if code not in snx_data: 
                        snx_data[code] = {'tech': tech, 'X': 0.0, 'Y': 0.0, 'Z': 0.0}
                    
                    if axis == 'STAX': snx_data[code]['X'] = val
                    elif axis == 'STAY': snx_data[code]['Y'] = val
                    elif axis == 'STAZ': snx_data[code]['Z'] = val

        # ==========================================
        # 3. K-PROTOCOL Data Processing
        # ==========================================
        rows_spatial = []
        for code, data in snx_data.items():
            if data['X'] != 0 and data['Y'] != 0 and data['Z'] != 0:
                r_si = np.sqrt(data['X']**2 + data['Y']**2 + data['Z']**2)
                alt = r_si - R_EARTH
                g_loc = G_SI * ((R_EARTH/r_si)**2)
                s_loc = (np.pi**2)/g_loc
                rows_spatial.append([code, data['tech'], r_si, alt, g_loc, s_loc, data['X'], data['Y'], data['Z']])

        slr_list = [r for r in rows_spatial if r[1] == 'L']
        vlbi_list = [r for r in rows_spatial if r[1] == 'R']
        gnss_list = [r for r in rows_spatial if r[1] == 'P']
        
        rows_multi = []
        
        # [핵심] 1순위: SLR vs VLBI (30km 이내 근접 관측소 3D 강제 매칭)
        for slr in slr_list:
            for vlbi in vlbi_list:
                dist_3d = np.sqrt((slr[6]-vlbi[6])**2 + (slr[7]-vlbi[7])**2 + (slr[8]-vlbi[8])**2)
                if dist_3d < 30000:
                    r1, r2 = slr[2], vlbi[2]
                    avg_r = (r1 + r2) / 2
                    sloc = (np.pi**2)/(G_SI * ((R_EARTH/avg_r)**2))
                    k_diff = abs(r1/sloc - r2/sloc)
                    rows_multi.append([f"{slr[0]} (SLR) & {vlbi[0]} (VLBI)", "SLR vs VLBI", r1, r2, abs(r1-r2), sloc, k_diff])
        
        # 2순위: VLBI가 없을 경우 SLR vs GNSS 매칭 (데이터 공백 방지)
        if not rows_multi:
            for slr in slr_list:
                for gnss in gnss_list:
                    dist_3d = np.sqrt((slr[6]-gnss[6])**2 + (slr[7]-gnss[7])**2 + (slr[8]-gnss[8])**2)
                    if dist_3d < 10000:
                        r1, r2 = slr[2], gnss[2]
                        avg_r = (r1 + r2) / 2
                        sloc = (np.pi**2)/(G_SI * ((R_EARTH/avg_r)**2))
                        k_diff = abs(r1/sloc - r2/sloc)
                        rows_multi.append([f"{slr[0]} (SLR) & {gnss[0]} (GNSS)", "SLR vs GNSS", r1, r2, abs(r1-r2), sloc, k_diff])

        df_spatial = pd.DataFrame(rows_spatial, columns=['ID', 'Technique', 'SI_Dist', 'Altitude', 'g_loc', 'S_loc', 'X', 'Y', 'Z'])
        df_multi = pd.DataFrame(rows_multi, columns=['Colocated Sites', 'Compare', 'R1 (SI)', 'R2 (SI)', 'SI_Diff (m)', 'S_loc', 'K_Diff (m)'])

        # ==========================================
        # 4. Dashboard UI
        # ==========================================
        if not df_multi.empty:
            st.markdown('<div class="multi-box">', unsafe_allow_html=True)
            st.markdown("### 🔭 The Absolute Proof: Multi-Technique Discrepancy")
            st.markdown("동일한 부지(30km 이내)에 위치한 레이저(SLR)와 전파(VLBI) 측정소의 척도 불일치입니다. K-PROTOCOL의 텐서($S_{loc}$)를 적용한 후 **K_Diff**가 어떻게 보정되는지 확인하십시오.")
            st.dataframe(df_multi.style.format('{:.5f}'), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        if not df_spatial.empty:
            df_spatial['K_Dist'] = df_spatial['SI_Dist'] / df_spatial['S_loc']
            df_spatial['Residual'] = df_spatial['SI_Dist'] - df_spatial['K_Dist']
            corr, _ = pearsonr(df_spatial['Altitude'], df_spatial['Residual'])
            
            c1, c2 = st.columns(2)
            c1.metric("총 분석된 관측소 개수", f"{len(df_spatial)} 개")
            c2.metric("공간 왜곡 보정률 (R²)", f"{(corr**2)*100:.7f} %")
            
            st.subheader("🌐 Spatial Calibration Results")
            st.plotly_chart(px.scatter(df_spatial, x='Altitude', y='Residual', hover_data=['ID', 'Technique'], trendline="ols", template="plotly_white"), use_container_width=True)
            
            st.markdown("#### Station Raw Data")
            st.dataframe(df_spatial[['ID', 'Technique', 'SI_Dist', 'Altitude', 'g_loc', 'S_loc', 'Residual']], use_container_width=True)
