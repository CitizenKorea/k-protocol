import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import gzip
from fpdf import FPDF
import io

# 1. K-PROTOCOL 글로벌 핵심 공리
G_SI = 9.80665
S_EARTH = (np.pi**2) / G_SI
C_SI = 299792458
R_EARTH = 6371000 # 지구 평균 반지름 (m)

st.set_page_config(page_title="K-PROTOCOL Omni-Center", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .report-title { font-size: 28px; font-weight: bold; color: #1f77b4; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 2. PDF 생성 엔진 (오류 완벽 수리)
def create_pdf(summary_df, data_type, unit):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(190, 10, f"K-PROTOCOL {data_type} NANO-REPORT", 0, 1, 'C')
    pdf.set_font("helvetica", '', 11)
    pdf.ln(10)
    pdf.cell(190, 8, f"Base Geometric Standard (S_earth): {S_EARTH:.9f}", 0, 1, 'L')
    pdf.ln(5)
    
    pdf.set_fill_color(220, 230, 241)
    pdf.cell(30, 10, "Target ID", 1, 0, 'C', True)
    pdf.cell(40, 10, f"SI Standard ({unit})", 1, 0, 'C', True)
    pdf.cell(40, 10, f"K-Protocol ({unit})", 1, 0, 'C', True)
    pdf.cell(35, 10, "Sync (%)", 1, 0, 'C', True)
    pdf.cell(45, 10, f"Rem. Var ({unit})", 1, 1, 'C', True)
    
    pdf.set_font("helvetica", '', 9)
    for _, row in summary_df.head(40).iterrows():
        pdf.cell(30, 10, str(row['ID'])[:15], 1, 0, 'C')
        si_val = f"{row['SI 기준']:,.4f}" if "m" in unit else f"{row['SI 기준']:.6f}"
        k_val = f"{row['K-Protocol']:,.4f}" if "m" in unit else f"{row['K-Protocol']:.6f}"
        rem_val = f"{row['남는변수']:,.6f}" if "m" in unit else f"{row['남는변수']:.9f}"
        
        pdf.cell(40, 10, si_val, 1, 0, 'C')
        pdf.cell(40, 10, k_val, 1, 0, 'C')
        pdf.cell(35, 10, f"{row['보정율 (%)']:.4f}", 1, 0, 'C')
        pdf.cell(45, 10, rem_val, 1, 1, 'C')
        
    # PDF 바이너리 에러 방지용 호환성 코드
    out = pdf.output(dest='S')
    return out.encode('latin-1') if isinstance(out, str) else bytes(out)

# 3. 사이드바
with st.sidebar:
    st.title("🔬 Omni Control")
    st.divider()
    st.write(f"**글로벌 왜곡 지수 ($S_e$):**\n`{S_EARTH:.9f}`")

st.title("🛰️ K-PROTOCOL 만물(OMNI) 정밀 분석 센터")
st.markdown("#### 우주 시간과 지구 3D 고도의 기하학적 왜곡을 추적합니다.")

uploaded_file = st.file_uploader("파일(SP3, CLK, SNX, CSV, XLSX, GZ 등)을 업로드하세요", 
                                 type=["sp3", "gz", "clk", "snx", "csv", "xlsx", "txt"])

if uploaded_file:
    fname = uploaded_file.name.lower()
    full_df = pd.DataFrame()
    data_type_name = "UNIVERSAL"
    unit_str = "Unit"
    
    try:
        with st.spinner("🚀 데이터를 나노 단위로 해독 및 3D 고도를 추적 중입니다..."):
            
            # --- A. 지상 좌표 데이터 (SINEX 3D 고도 추적 엔진) ---
            if ".snx" in fname:
                data_type_name = "3D GEODETIC (고도/중력 추적)"
                unit_str = "m"
                snx_coords = {}
                
                if fname.endswith('.gz'):
                    file_iterator = gzip.open(uploaded_file, 'rt', encoding='utf-8', errors='ignore')
                else:
                    file_iterator = io.TextIOWrapper(uploaded_file, encoding='utf-8', errors='ignore')
                
                capture = False
                for line in file_iterator:
                    if line.startswith('+SOLUTION/ESTIMATE'): capture = True; continue
                    if line.startswith('-SOLUTION/ESTIMATE'): capture = False; break
                    if capture and any(axis in line for axis in ['STAX', 'STAY', 'STAZ']):
                        p = line.split()
                        if len(p) >= 9:
                            sta_id = p[2]
                            axis = p[1]
                            try:
                                if sta_id not in snx_coords: snx_coords[sta_id] = {}
                                snx_coords[sta_id][axis] = float(p[8])
                            except ValueError: pass
                
                rows = []
                for sta_id, coords in snx_coords.items():
                    if 'STAX' in coords and 'STAY' in coords and 'STAZ' in coords:
                        # 3D 절대 거리(R) 계산
                        R = np.sqrt(coords['STAX']**2 + coords['STAY']**2 + coords['STAZ']**2)
                        # 고도 계산
                        altitude = R - R_EARTH
                        # 국소 중력 계산 (간단한 자유공간 이상 모델)
                        g_loc = G_SI * ((R_EARTH / R)**2)
                        # 국소 왜곡 지수
                        s_loc = (np.pi**2) / g_loc
                        rows.append([sta_id, R, altitude, g_loc, s_loc])
                        
                full_df = pd.DataFrame(rows, columns=['ID', 'SI 기준', '고도(m)', '국소중력', 'S_loc'])

            # --- B. 시간/일반 데이터 처리 ---
            elif any(ext in fname for ext in ['.sp3', '.clk']):
                data_type_name = "GNSS SATELLITE (시간 오차)"
                unit_str = "μs"
                rows = []
                file_iterator = gzip.open(uploaded_file, 'rt', encoding='utf-8', errors='ignore') if fname.endswith('.gz') else io.TextIOWrapper(uploaded_file, encoding='utf-8', errors='ignore')
                
                for line in file_iterator:
                    if ".sp3" in fname and line.startswith('P'): 
                        try: rows.append([line[1:4].strip(), float(line[46:60])])
                        except ValueError: pass
                    elif ".clk" in fname and line.startswith('AS'):
                        p = line.split()
                        if len(p) >= 10: 
                            try: rows.append([p[1], float(p[9])*1e6])
                            except ValueError: pass
                full_df = pd.DataFrame(rows, columns=['ID', 'SI 기준'])
                
            else:
                data_type_name = "GENERIC / INDUSTRIAL"
                temp_df = pd.read_csv(uploaded_file) if fname.endswith(('.csv', '.txt')) else pd.read_excel(uploaded_file)
                numeric_cols = temp_df.select_dtypes(include=np.number).columns.tolist()
                if numeric_cols:
                    col_c1, col_c2 = st.columns(2)
                    target_col = col_c1.selectbox("보정할 측정값 컬럼", numeric_cols)
                    id_col = col_c2.selectbox("데이터 구분용 ID 컬럼", ['인덱스 자동 부여'] + list(temp_df.columns))
                    full_df['ID'] = temp_df.index.astype(str) if id_col == '인덱스 자동 부여' else temp_df[id_col].astype(str)
                    full_df['SI 기준'] = temp_df[target_col].astype(float)
                    unit_str = st.text_input("데이터의 단위 (예: nm, %)", value="Unit")

            # --- 4. 나노 분석 엔진 (고도/국소 중력 연동) ---
            if not full_df.empty:
                full_df = full_df.dropna()
                
                # S_loc (고도 반영 왜곡 지수)가 있으면 그것을 쓰고, 없으면 글로벌 S_EARTH 사용
                distortion_factor = full_df['S_loc'] if 'S_loc' in full_df.columns else S_EARTH
                
                full_df['K-Protocol'] = np.float64(full_df['SI 기준']) / distortion_factor
                full_df['남는변수'] = np.float64(full_df['SI 기준']) - full_df['K-Protocol']
                full_df['보정율 (%)'] = np.where(full_df['SI 기준'] == 0, 100.0, (full_df['K-Protocol'] / full_df['SI 기준']).abs() * 100)

                st.subheader(f"📋 {data_type_name} 전수조사 요약")
                
                agg_dict = {'SI 기준': 'mean', 'K-Protocol': 'mean', '보정율 (%)': 'mean', '남는변수': 'mean'}
                if '고도(m)' in full_df.columns:
                    agg_dict.update({'고도(m)': 'mean', '국소중력': 'mean', 'S_loc': 'mean'})
                    
                summary = full_df.groupby('ID').agg(agg_dict).reset_index()
                st.dataframe(summary, use_container_width=True)

                st.divider()
                sel_id = st.selectbox("🎯 상세 분석 대상 선택", summary['ID'].unique())
                sat_data = full_df[full_df['ID'] == sel_id].copy().reset_index()

                st.subheader(f"📈 실시간 정밀 지표: {sel_id}")
                
                # 고도 추적 UI 렌더링
                if '고도(m)' in sat_data.columns:
                    st.info(f"🌍 이 관측소는 3D 추적 결과, 평균 고도 **{sat_data['고도(m)'].iloc[-1]:,.2f}m**에 위치해 있으며, 해당 고도의 국소 왜곡 지수($S_{{loc}}$ = {sat_data['S_loc'].iloc[-1]:.9f})가 적용되었습니다.")
                
                c1, c2, c3, c4 = st.columns(4)
                last = sat_data.iloc[-1]
                
                c1.metric(f"SI 절대 거리 ({unit_str})", f"{last['SI 기준']:,.4f}" if unit_str=='m' else f"{last['SI 기준']:.6f}")
                c2.metric(f"K-Protocol 진실 거리 ({unit_str})", f"{last['K-Protocol']:,.4f}" if unit_str=='m' else f"{last['K-Protocol']:.6f}")
                c3.metric("보정율 (Sync)", f"{last['보정율 (%)']:.4f}%")
                c4.metric(f"순수 남는변수 ({unit_str})", f"{last['남는변수']:,.4f}" if unit_str=='m' else f"{last['남는변수']:.9f}")

                fig = go.Figure()
                fig.add_trace(go.Scatter(y=sat_data['SI 기준'], name=f'SI Standard', line=dict(color='red')))
                fig.add_trace(go.Scatter(y=sat_data['K-Protocol'], name=f'K-Protocol', line=dict(color='blue')))
                fig.update_layout(yaxis_title=f"Measured Value ({unit_str})", hovermode="x unified", height=450)
                st.plotly_chart(fig, use_container_width=True)

                try:
                    pdf_bytes = create_pdf(summary, data_type_name, unit_str)
                    st.download_button("📄 글로벌 분석 리포트 PDF 다운로드", pdf_bytes, "K_Report_Omni.pdf", "application/pdf")
                except Exception as e:
                    st.error(f"PDF 생성 오류: {e}")
            else:
                st.warning("⚠️ 파일에서 데이터를 추출하지 못했습니다.")
    except Exception as e:
        st.error(f"데이터 처리 중 알 수 없는 오류가 발생했습니다: {e}")
