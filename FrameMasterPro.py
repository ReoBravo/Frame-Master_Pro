import streamlit as st
from PIL import Image
import io
import zipfile
import fitz  # PyMuPDF

# --- [1. 보안 및 페이지 설정] ---
st.set_page_config(page_title="Frame Master Pro", layout="wide")

# 보안을 위한 최대 파일 용량 제한 (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024 

# 디자인 설정: 모든 디테일을 하나하나 완벽하게 고정
st.markdown("""
    <style>
    /* 메인 배경색 (하늘색) */
    .main { background-color: #e3f2fd; color: #333333; }
    .stApp { background-color: #e3f2fd; }
    
    /* 사이드바 바탕색 (밝은 파랑) */
    [data-testid="stSidebar"] { background-color: #64b5f6; color: #ffffff; }
    
    /* 좌측 설정 박스 블랙 & 텍스트/숫자 흰색 */
    div[data-baseweb="select"] > div, 
    div[data-baseweb="input"],
    div[data-baseweb="base-input"] {
        background-color: #000000 !important;
        color: #ffffff !important;
        border-radius: 8px !important;
    }
    input {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    div[data-baseweb="select"] span {
        color: #ffffff !important;
    }

   /* [최종 교정] 우측 상단 헤더 전체 블랙 & 모든 아이콘/글자를 하늘색으로 고정 */
    header[data-testid="stHeader"] {
        background-color: #000000 !important;
    }
    
    /* 왼쪽 >> 버튼, 오른쪽 Share, Fork, 점 세 개 아이콘 모두 하늘색으로 */
    header[data-testid="stHeader"] button,
    header[data-testid="stHeader"] a,
    header[data-testid="stHeader"] svg,
    header[data-testid="stHeader"] span {
        color: #64b5f6 !important; /* 사이드바와 동일한 밝은 하늘색 */
        fill: #64b5f6 !important;  /* 아이콘 색상 고정 */
        -webkit-text-fill-color: #64b5f6 !important;
    }

    /* 깃허브 아이콘만 원래 색상 유지 (선택 사항) */
    header[data-testid="stHeader"] a[href*="github"] svg {
        fill: inherit !important;
    }

    /* 깃허브 아이콘은 제외 (기존 스타일 유지 시도) */
    header[data-testid="stHeader"] a[href*="github"] svg {
        fill: inherit !important; /* 또는 박사님이 원하시는 특정 색상값 */
    }

    /* [교정] 업로드 박스 디자인 최종 정리 */
    div[data-testid="stFileUploader"] section {
        background-color: #000000 !important;
        border: 1px solid #444444 !important;
    }
    /* 박스 내부 안내문구: 흰색 강제 */
    div[data-testid="stFileUploader"] label, 
    div[data-testid="stFileUploader"] div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stFileUploader"] small,
    div[data-testid="stFileUploader"] span {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    /* 업로드 아이콘 흰색 */
    div[data-testid="stFileUploader"] svg {
        fill: #ffffff !important;
        color: #ffffff !important;
    }
    /* [박사님 지적 사항 반영] Browse files 버튼: 흰색 바탕에 "검정색" 텍스트 강제 */
    /* Browse files 버튼: 배경을 밝은 파랑으로, 텍스트는 검정색으로 */
    div[data-testid="stFileUploader"] button {
        background-color: #64b5f6 !important; /* 왼쪽 메뉴와 같은 밝은 파랑 */
        color: #000000 !important;             /* 글자색 검정 */
        border: none !important;
    }
    /* 버튼 내부 레이블 색상도 검정으로 고정 */
    div[data-testid="stFileUploader"] button div {
        color: #000000 !important;
    }

    /* 업로드 안내 블랙바 */
    .upload-bar { 
        background-color: #000000; 
        color: #ffffff; 
        padding: 10px; 
        border-radius: 8px 8px 0 0; 
        font-weight: bold;
        text-align: center;
        margin-bottom: -10px;
    }

    /* 메인 타이틀 색상 (밝은 파랑) */
    .main-title { color: #64b5f6; font-family: 'Inter', sans-serif; font-weight: 800; font-size: 3.5rem; margin-top: -20px; }
    .info-text { color: #555555; font-size: 0.85rem; margin-top: -15px; font-style: italic; }
    
    /* 보안 박스 (슬림 디자인) */
    .security-info {
        background-color: #ffffff;
        border: 1px solid #ffab40;
        border-radius: 6px;
        padding: 4px 8px; 
        margin-top: 10px;
        margin-bottom: 5px;
        color: #1a237e;
        font-size: 0.75rem; 
        font-weight: bold;
        width: 90%;
        text-align: center;
        line-height: 1.3;
    }
    
    .sb-label { color: #ffffff !important; font-weight: bold; font-size: 1.0rem; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- [2. 로직: 이미지 처리] ---
def transform_frame(img, target_ratio_name):
    img = img.convert("RGB")
    tw, th = (1080, 1920) if "9:16" in target_ratio_name else (1920, 1080)
    target_ratio = tw / th
    orig_w, orig_h = img.size
    orig_ratio = orig_w / orig_h
    if orig_ratio > target_ratio:
        nh, nw = th, int(th * orig_ratio)
    else:
        nw, nh = tw, int(tw / orig_ratio)
    resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left, top = (nw - tw) // 2, (nh - th) // 2
    return resized.crop((left, top, left + tw, top + th))

# --- [3. 사이드바 설정] ---
with st.sidebar:
    st.markdown("<div style='height: 55px;'></div>", unsafe_allow_html=True)
    st.markdown("<p class='sb-label'>⚙️ 목표 프레임 비율</p>", unsafe_allow_html=True)
    target_ratio_name = st.selectbox("RatioSelect", ["9:16 (Shorts)", "16:9 (Wide)"], label_visibility="collapsed")
    
    st.divider()
    st.markdown("<p class='sb-label'>📐 그리드(Grid) 설정</p>", unsafe_allow_html=True)
    col_c, col_r = st.columns(2)
    grid_cols = col_c.number_input("가로 칸 수", 1, 10, 5)
    grid_rows = col_r.number_input("세로 줄 수", 1, 10, 4)
    
    st.markdown("<p class='sb-label' style='font-size:0.9rem; margin-top:10px;'>최대 추출 개수</p>", unsafe_allow_html=True)
    max_frames = st.number_input("MaxCount", 1, 100, 20, label_visibility="collapsed")
    
    st.divider()
    st.markdown("""<div class='security-info'>Security Processed<br>(Volatile processing in memory)</div>""", unsafe_allow_html=True)
    st.caption("Kwon_Jeong Edition")

# --- [3.5 생일 축하 이벤트] ---
if "celebrated" not in st.session_state: st.session_state.celebrated = False
if not st.session_state.celebrated:
    @st.dialog("🎂 Happy Birthday to You! 🎂")
    def birthday_popup():
        st.write("==========================================")
        st.write("### 🎬 Kwon_Jeong의 Frame Master Pro")
        st.write("### 🎈 2026.4.10 / 08")
        st.write("#### **동호회 회원 여러분, 환영합니다!**")
        st.write("==========================================")
        st.write("Kwon &Jeong 님과 생신을 맞이하신 모든 분들께 진심으로 축하를 전합니다!")
        if st.button("감사합니다! 앱 시작하기 (Enter)", use_container_width=True):
            st.session_state.celebrated = True
            st.rerun()
    birthday_popup()
    st.stop()

# --- [4. 메인 화면 및 파일 처리] ---
st.markdown("<h1 class='main-title'>Frame Master Pro</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #ffab40; font-size: 1.1rem; font-weight: bold; margin-top: -15px;'>Precision Extraction & Full-Fill Security Engine</p>", unsafe_allow_html=True)
st.markdown("<p class='info-text'>You can achieve as much as you believe you can.</p>", unsafe_allow_html=True)

st.markdown("<p style='color: #ffab40; font-weight: bold; margin-bottom: 5px; margin-top: 25px;'>📂 스토리보드 파일 업로드 (PDF, PNG, JPG)</p>", unsafe_allow_html=True)
st.markdown("<div class='upload-bar'>↑ Click or Drag files here to start</div>", unsafe_allow_html=True)
uploaded_file = st.file_uploader("Uploader", type=["pdf", "png", "jpg", "jpeg"], label_visibility="collapsed")

if uploaded_file:
    if uploaded_file.size > MAX_FILE_SIZE:
        st.error("보안 정책상 10MB 이하의 파일만 허용됩니다.")
    else:
        st.success(f"준비 완료: {uploaded_file.name}")
        if st.button("🚀 에셋 생성 및 압축 시작"):
            status = st.empty()
            status.write("🏃‍♂️💨 작업을 시작합니다... 🏅🥇")
            zip_buffer = io.BytesIO()
            total_count = 1
            file_ext = uploaded_file.name.split('.')[-1].lower()
            try:
                with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zip_file:
                    if file_ext == 'pdf':
                        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                        for i in range(len(doc)):
                            if total_count > max_frames: break
                            pix = doc.load_page(i).get_pixmap(matrix=fitz.Matrix(3, 3))
                            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                            final_img = transform_frame(img, target_ratio_name)
                            img_io = io.BytesIO()
                            final_img.save(img_io, format='PNG')
                            zip_file.writestr(f"frame_{total_count:02d}.png", img_io.getvalue())
                            total_count += 1
                        doc.close()
                    else:
                        img = Image.open(uploaded_file)
                        W, H = img.size
                        cw, ch = W // grid_cols, H // grid_rows
                        for r in range(grid_rows):
                            for c in range(grid_cols):
                                if total_count > max_frames: break
                                crop_img = img.crop((c*cw, r*ch, min((c+1)*cw, W), min((r+1)*ch, H)))
                                final_img = transform_frame(crop_img, target_ratio_name)
                                img_io = io.BytesIO()
                                final_img.save(img_io, format='PNG')
                                zip_file.writestr(f"frame_{total_count:02d}.png", img_io.getvalue())
                                total_count += 1
                st.download_button(label="📂 추출 에셋 다운로드 (ZIP)", data=zip_buffer.getvalue(), file_name="FrameMaster_Assets.zip", mime="application/zip", use_container_width=True)
                st.balloons()
            except Exception as e:
                st.error(f"오류 발생: {e}")
