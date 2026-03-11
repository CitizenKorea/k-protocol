import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import gzip
from fpdf import FPDF
import io

# 1. K-PROTOCOL 핵심 물리 공리
G_SI = 9.80665
S_EARTH = (np.pi**2) / G_SI
C_SI = 299792458
C_K = C_SI / S_EARTH

st.set_page_config(page_title="K-PROTOCOL Omni-Center", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .report-title { font-size: 28px; font-weight: bold; color: #1f77b4; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 2. PDF 생성 엔진
def create_pdf(summary_df, data_type):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(190, 10, f"K-PROTOCOL {data_type} NANO-REPORT", 0, 1, 'C')
    pdf.set_font("helvetica", '', 11)
    pdf.ln(10)
    pdf.cell(190, 8, f"Geometric Standard (S_earth): {S_EARTH:.9f}", 0, 1, 'L')
    pdf.ln(5)
    
    pdf.set_fill_color(220, 230, 241)
    pdf.cell(30, 10, "Target ID", 1, 0, 'C', True)
    pdf.cell(40, 10, "SI Standard", 1, 0, 'C', True)
    pdf.cell(40, 10, "K-Protocol", 1, 0, 'C', True)
    pdf.cell(35, 10, "Sync (%)", 1, 0, 'C', True)
    pdf.cell(45, 10, "Rem. Var", 1, 1, 'C', True)
    
    pdf.set_font("helvetica", '', 9)
    for _, row in summary_df.head(40).iterrows():
        pdf.cell(30, 10, str(row['ID'])[:15], 1, 0, 'C')
        pdf.cell(40, 10, f"{row['SI 기준']:.6f}", 1, 0, 'C')
        pdf.cell(40, 10, f"{row['K-Protocol']:.6f}", 1, 0, 'C')
        pdf.cell(35, 10, f"{row['보정율 (%)']:.4f}", 1, 0, 'C')
        pdf.cell(45, 10, f"{row['남는변수']:.9f}", 1, 1, 'C')
    return bytes(pdf.output())

# 3. 사이드바
with st.sidebar:
    st.title("🔬 Omni Control")
    st.divider()
    st.write(f"**왜곡 지수 ($S_e$):**\n`{S_EARTH:.9f}`")
    st.write(f"**절대 광속 ($c_k$):**\n`{C_K:,.1f} m/s`")

st.title("🛰️ K-PROTOCOL 만물(OMNI) 정밀 분석 센터")
st.markdown("#### 우주, 지구, 그리고 산업의 모든 데이터를 소수점 9자리로 해체합니다.")

uploaded_file = st.file_uploader("분석할 파일을 업로드하세요 (SP3, CLK, SNX, CSV, XLSX, GZ 등)", 
                                 type=["sp3", "gz", "clk", "snx", "csv", "xlsx", "txt"])

if uploaded_file:
    fname = uploaded_file.name.lower()
    full_df = pd.DataFrame()
    data_type_name = "UNIVERSAL"
    
    try:
        with st.spinner("🚀 데이터를 나노 단위로 해독 중입니다... (거대 파일은 1~2분 소요)"):
            
            # --- A. 특수 GNSS 데이터 (초고속 스트리밍 읽기 적용) ---
            if any(ext in fname for ext in ['.sp3', '.clk', '.snx']):
                data_type_name = "GNSS / GEODETIC"
                rows = []
                
                # 메모리 폭발 방지용 진정한 한 줄 읽기 모드
                if fname.endswith('.gz'):
                    file_iterator = gzip.open(uploaded_file, 'rt', encoding='utf-8', errors='ignore')
                else:
                    file_iterator = io.TextIOWrapper(uploaded_file, encoding='utf-8', errors='ignore')
                
                if ".snx" in fname:
                    capture = False
                    for line in file_iterator:
                        if line.startswith('+SOLUTION/ESTIMATE'): capture = True; continue # 철자 수정 완료!
                        if line.startswith('-SOLUTION/ESTIMATE'): capture = False; break
                        if capture and 'STAX' in line:
                            p = line.split()
                            if len(p) >= 9:
                                try: rows.append([p[2], float(p[8])])
                                except ValueError: pass
                                
                elif ".sp3" in fname:
                    for line in file_iterator:
                        if line.startswith('P'): 
                            try: rows.append([line[1:4].strip(), float(line[46:60])])
                            except ValueError: pass
                            
                elif ".clk" in fname:
                    for line in file_iterator:
                        if line.startswith('AS'):
                            p = line.split()
                            if len(p) >= 10: 
                                try: rows.append([p[1], float(p[9])*1e6])
                                except ValueError: pass
                
                full_df = pd.DataFrame(rows, columns=['ID', 'SI 기준'])

            # --- B. 만물 일반 데이터 파싱 (CSV, 엑셀) ---
            else:
                data_type_name = "GENERIC / INDUSTRIAL"
                if fname.endswith('.csv') or fname.endswith('.txt'):
                    temp_df = pd.read_csv(uploaded_file)
                elif fname.endswith('.xlsx'):
                    temp_df = pd.read_excel(uploaded_file)
                    
                numeric_cols = temp_df.select_dtypes(include=np.number).columns.tolist()
                
                if numeric_cols:
                    st.info("💡 일반 데이터 감지. 보정할 측정값(오차)과 식별자(ID) 컬럼을 선택해 주세요.")
                    col_c1, col_c2 = st.columns(2)
                    target_col = col_c1.selectbox("보정할 측정값 컬럼", numeric_cols)
                    id_col = col_c2.selectbox("데이터 구분용 ID 컬럼", ['인덱스 자동 부여'] + list(temp_df.columns))
                    
                    if id_col == '인덱스 자동 부여': full_df['ID'] = temp_df.index.astype(str)
                    else: full_df['ID'] = temp_df[id_col].astype(str)
                        
                    full_df['SI 기준'] = temp_df[target_col].astype(float)

            # --- 4. 공통 나노 분석 계산 및 출력 ---
            if not full_df.empty:
                full_df = full_df.dropna()
                
                full_df['K-Protocol'] = np.float64(full_df['SI 기준']) / S_EARTH
                full_df['남는변수'] = np.float64(full_df['SI 기준']) - full_df['K-Protocol']
                full_df['보정율 (%)'] = np.where(
                    full_df['SI 기준'] == 0, 100.0, 
                    (full_df['K-Protocol'] / full_df['SI 기준']).abs() * 100
                )

                st.subheader(f"📋 {data_type_name} 전수조사 요약")
                summary = full_df.groupby('ID').agg({
                    'SI 기준': 'mean', 'K-Protocol': 'mean', 
                    '보정율 (%)': 'mean', '남는변수': 'mean'
                }).reset_index()
                
                # 에러 원인이었던 색칠 기능 제거, 순수하고 빠른 표 출력
                st.dataframe(summary.style.format({
                    'SI 기준': '{:.6f}', 'K-Protocol': '{:.6f}', 
                    '보정율 (%)': '{:.4f}%', '남는변수': '{:.9f}'
                }), use_container_width=True)

                st.divider()
                sel_id = st.selectbox("🎯 상세 분석 대상 선택", summary['ID'].unique())
                sat_data = full_df[full_df['ID'] == sel_id].copy().reset_index()
                
                if "GNSS" in data_type_name and str(sel_id).startswith('R'):
                    st.warning("⚠️ GLONASS(R) 노이즈 필터링 적용 중...")
                    sat_data['SI 기준'] = sat_data['SI 기준'].rolling(window=10).mean()
                    sat_data['K-Protocol'] = sat_data['K-Protocol'].rolling(window=10).mean()

                st.subheader(f"📈 실시간 정밀 지표: {sel_id}")
                c1, c2, c3, c4 = st.columns(4)
                last = sat_data.iloc[-1]
                
                c1.metric("SI 기준", f"{last['SI 기준']:.6f}")
                c2.metric("K-Protocol", f"{last['K-Protocol']:.6f}")
                c3.metric("보정율 (Sync)", f"{last['보정율 (%)']:.4f}%")
                c4.metric("남는변수", f"{last['남는변수']:.9f}")

                fig = go.Figure()
                fig.add_trace(go.Scatter(y=sat_data['SI 기준'], name='SI Standard', line=dict(color='red')))
                fig.add_trace(go.Scatter(y=sat_data['K-Protocol'], name='K-Protocol', line=dict(color='blue')))
                fig.update_layout(yaxis_title="Measured Value", hovermode="x unified", height=450)
                st.plotly_chart(fig, use_container_width=True)

                try:
                    pdf_bytes = create_pdf(summary, data_type_name)
                    st.download_button("📄 글로벌 분석 리포트 PDF 다운로드", pdf_bytes, "K_Report_Omni.pdf", "application/pdf")
                except Exception as e:
                    st.error(f"PDF 생성 오류: {e}")
            else:
                st.warning("⚠️ 파일에서 데이터를 추출하지 못했습니다. 형식이 맞는지 확인해 주세요.")

    except Exception as e:
        st.error(f"데이터 처리 중 알 수 없는 오류가 발생했습니다: {e}")
