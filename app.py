import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gzip
import io
import os
import requests
import math
from scipy.stats import pearsonr
from scipy.spatial import KDTree
from fpdf import FPDF
import datetime

# ==========================================
# 1. 핵심 물리 엔진 (Physics Engine)
# ==========================================
g_SI = 9.80665  
S_EARTH = (np.pi**2) / g_SI
C_SI = 299792458
R_EARTH = 6371000

def ecef_to_wgs84(x, y, z):
    a = 6378137.0
    e2 = 0.00669437999014
    b = math.sqrt(a**2 * (1 - e2))
    ep2 = (a**2 - b**2) / b**2
    p = math.sqrt(x**2 + y**2)
    th = math.atan2(a * z, b * p)
    lon = math.atan2(y, x)
    lat = math.atan2((z + ep2 * b * math.sin(th)**3), (p - e2 * a * math.cos(th)**3))
    N = a / math.sqrt(1 - e2 * math.sin(lat)**2)
    alt = p / math.cos(lat) - N
    return math.degrees(lat), math.degrees(lon), alt

def wgs84_gravity(lat_deg, alt):
    lat = math.radians(lat_deg)
    ge = 9.7803253359 
    k = 0.00193185265241
    e2 = 0.00669437999013
    g0 = ge * (1 + k * math.sin(lat)**2) / math.sqrt(1 - e2 * math.sin(lat)**2)
    fac = - (3.087691e-6 - 4.3977e-9 * math.sin(lat)**2) * alt + 0.72125e-12 * alt**2
    return g0 + fac

def quaternion_to_euler_vectorized(q0, q1, q2, q3):
    sinr_cosp = 2 * (q0 * q1 + q2 * q3)
    cosr_cosp = 1 - 2 * (q1**2 + q2**2)
    roll = np.arctan2(sinr_cosp, cosr_cosp)
    sinp = 2 * (q0 * q2 - q3 * q1)
    pitch = np.where(np.abs(sinp) >= 1, np.sign(sinp) * np.pi / 2, np.arcsin(np.clip(sinp, -1, 1)))
    siny_cosp = 2 * (q0 * q3 + q1 * q2)
    cosy_cosp = 1 - 2 * (q2**2 + q3**2)
    yaw = np.arctan2(siny_cosp, cosy_cosp)
    return np.degrees(yaw), np.degrees(pitch), np.degrees(roll)

# ==========================================
# 2. 통합 파싱 엔진 (Universal Parser)
# ==========================================
def universal_parser(content_lines, fname):
    data_store = {
        'obx': pd.DataFrame(), 'erp': pd.DataFrame(), 
        'tro': pd.DataFrame(), 'inx': pd.DataFrame(), 'tec': pd.DataFrame()
    }
    try:
        if ".obx" in fname:
            rows, curr_epoch = [], "Unknown"
            for line in content_lines:
                if line.startswith('##'):
                    p = line.split()
                    if len(p) > 6: curr_epoch = f"{p[1]}-{p[2]}-{p[3]} {p[4]}:{p[5]}"
                elif 'ATT ' in line:
                    p = line.split()
                    if len(p) >= 7:
                        prn, q0, q1, q2, q3 = p[1], float(p[3]), float(p[4]), float(p[5]), float(p[6])
                        rows.append([curr_epoch, prn, q0, q1, q2, q3])
            if rows:
                df = pd.DataFrame(rows, columns=['Epoch', 'Satellite_ID', 'q0', 'q1', 'q2', 'q3'])
                df['Norm'] = np.sqrt(df['q0']**2 + df['q1']**2 + df['q2']**2 + df['q3']**2)
                df['Yaw'], df['Pitch'], df['Roll'] = quaternion_to_euler_vectorized(df['q0'], df['q1'], df['q2'], df['q3'])
                data_store['obx'] = df

        elif ".erp" in fname:
            rows = []
            for line in content_lines:
                p = line.split()
                if len(p) >= 5 and p[0].replace('.','',1).isdigit():
                    rows.append([float(p[0]), float(p[1]), float(p[2]), float(p[3]), float(p[4])])
            if rows:
                data_store['erp'] = pd.DataFrame(rows, columns=['MJD', 'X_Pole', 'Y_Pole', 'UT1_UTC', 'LOD'])

        elif ".tro" in fname:
            sites, sols = {}, []
            cap_site, cap_sol = False, False
            for line in content_lines:
                if '+SITE/ID' in line: cap_site = True
                elif '-SITE/ID' in line: cap_site = False
                elif '+TROP/SOLUTION' in line: cap_sol = True
                elif '-TROP/SOLUTION' in line: cap_sol = False
                if cap_site and not line.startswith('*') and len(line.split()) > 5:
                    p = line.split()
                    sites[p[0]] = float(p[-1])
                if cap_sol and not line.startswith('*') and len(line.split()) > 2:
                    p = line.split()
                    sols.append([p[0], p[1], float(p[2])])
            if sols:
                df = pd.DataFrame(sols, columns=['Site_ID', 'Epoch', 'ZTD'])
                df['Height'] = df['Site_ID'].map(sites)
                data_store['tro'] = df

        elif any(x in fname for x in ['.inx', '.nix', 'gim']):
            rows_inx, rows_tec = [], []
            curr_epoch, curr_lat, reading_tec = None, None, False
            for line in content_lines:
                if "PRN / BIAS / RMS" in line:
                    p = line.split()
                    rows_inx.append([p[0], float(p[1]), float(p[2])])
                elif "EPOCH OF CURRENT MAP" in line:
                    p = line.split()
                    curr_epoch = f"{p[0]}-{p[1]}-{p[2]} {p[3]}:{p[4]}"
                elif "LAT/LON1/LON2/DLON/H" in line:
                    curr_lat = float(line.split()[0])
                    reading_tec = True
                elif reading_tec and line.strip() and not line.startswith('END'):
                    vals = [float(v) for v in line.split()]
                    if vals: rows_tec.append([curr_epoch, curr_lat, vals[0]/10.0])
                    reading_tec = False
            data_store['inx'] = pd.DataFrame(rows_inx, columns=['PRN', 'Bias', 'RMS'])
            data_store['tec'] = pd.DataFrame(rows_tec, columns=['Epoch', 'Latitude', 'TEC'])
    except Exception as e:
        st.error(f"파싱 중 오류 발생: {e}")
    return data_store

# ==========================================
# 3. Streamlit UI 대시보드 (Part 2)
# ==========================================
st.set_page_config(page_title="K-PROTOCOL Omni Center", layout="wide")

st.title("🛰️ K-PROTOCOL Omni 분석 센터")
st.markdown("### 데이터로 증명하고 스스로 판단하십시오.")
st.divider()

# 파일 업로더
uploaded_file = st.file_uploader("궤도/보정 파일을 업로드하세요 (obx, erp, tro, nix, nix...)", type=["snx", "sp3", "clk", "obx", "erp", "tro", "inx", "nix", "gz"])

if uploaded_file:
    fname = uploaded_file.name.lower()
    # 파일 내용 읽기
    if fname.endswith('.gz'):
        with gzip.open(uploaded_file, 'rt', encoding='utf-8', errors='ignore') as f:
            content = f.read().splitlines()
    else:
        content = uploaded_file.read().decode('utf-8', errors='ignore').splitlines()
    
    # 데이터 파싱 호출
    data = universal_parser(content, fname)

    # --- 시각화 섹션 ---
    # A. OBX 분석
    if not data['obx'].empty:
        st.subheader("A. 위성 자세 데이터 (ATT.OBX)")
        df = data['obx']
        st.write(f"무결성 검증 (Norm Avg): {df['Norm'].mean():.6f}")
        sel_sat = st.selectbox("위성 선택", df['Satellite_ID'].unique())
        fig_obx = px.line(df[df['Satellite_ID']==sel_sat], x='Epoch', y=['Yaw', 'Pitch', 'Roll'], title=f"{sel_sat} 자세 변동")
        st.plotly_chart(fig_obx, use_container_width=True)

    # B. ERP 분석
    if not data['erp'].empty:
        st.subheader("B. 지구 자전 파라미터 (ERP)")
        df = data['erp']
        c1, c2 = st.columns(2)
        fig_pm = px.scatter(df, x='X_Pole', y='Y_Pole', color='MJD', title="극운동 궤적")
        c1.plotly_chart(fig_pm, use_container_width=True)
        fig_lod = px.line(df, x='MJD', y='LOD', title="자전 속도(LOD) 변화")
        c2.plotly_chart(fig_lod, use_container_width=True)

    # C. TRO 분석
    if not data['tro'].empty:
        st.subheader("C. 대류권 지연 (TRO)")
        df = data['tro']
        fig_ztd = px.line(df, x='Epoch', y='ZTD', color='Site_ID', title="ZTD 시계열")
        st.plotly_chart(fig_ztd, use_container_width=True)

    # D. TEC 분석
    if not data['tec'].empty:
        st.subheader("D. 전리층 격자 지도 (GIM)")
        df = data['tec']
        fig_tec = px.density_heatmap(df, x='Epoch', y='Latitude', z='TEC', color_continuous_scale='Turbo', title="TEC 히트맵")
        st.plotly_chart(fig_tec, use_container_width=True)

else:
    st.info("왼쪽 혹은 위쪽의 업로드 버튼을 눌러 분석할 파일을 선택해주세요.")

st.divider()
st.caption("© 2026 K-PROTOCOL Omni System | Patent Pending")
