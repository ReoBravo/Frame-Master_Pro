import streamlit as st
from PIL import Image
import io
import zipfile
import fitz  # PyMuPDF

# --- [1. 보안 및 페이지 설정] ---
st.set_page_config(page_title="Frame Master Pro", layout="wide") [cite: 2]

# 보안을 위한 최대 파일 용량 제한 (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024 

# 디자인 설정: 메인 영역 다크 모드 및 타이틀 색상 수정
st.markdown("""
    <style>
    /* 메인 배경색 (다크 스타일로 변경) */
    .main { background-color: #0e1117; color: #ffffff; } [cite: 2]
    .stApp { background-color: #0e1117; } [cite: 2]
    
    /* 사이드바 바탕색 (밝은 파랑 유지) */
    [data-testid="stSidebar"] { background-color: #64b5f6; color: #ffffff; } [cite: 2]
    
    /* 보안 박스 스타일 */
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
        text-align: center; [cite: 3, 4]
        line-height: 1.3;
    }
    
    /* 사이드바 내부 텍스트 */
    .sb-label { color: #ffffff !important; font-weight: bold; font-size: 1.0rem; margin-bottom: 5px; }
    
    /* 버튼 스타일 */
    .stButton>button {
        background: linear-gradient(90deg, #1e88e5 0%, #42a5f5 100%);
        color: white; border: none; border-radius: 10px; [cite: 5]
        padding: 0.5rem 2rem; font-weight: bold; width: 100%;
    }
    
    /* 메인 타이틀 및 텍스트 수정: 타이틀 색상을 사이드바 배경색과 동일한 밝은 파랑(#64b5f6)으로 변경 */
    .main-title { color: #64b5f6; font-family: 'Inter', sans-serif; font-weight: 800; font-size: 3.5rem; margin-top: -45px; } [cite: 7]
    .info-text { color: #bbbbbb; font-size: 0.85rem; margin-top: -15px; font-style: italic; } [cite: 8]
    
    /* 사이드바 폰트 색상 강제 */
    [data-testid="stSidebar"] .stMarkdown p { color: #ffffff !important; } [cite: 9]
    </style>
    """, unsafe_allow_html=True)

# --- [2. 로직: 비율 변환 및 꽉 채우기] ---
def transform_frame(img, target_ratio_name):
    img = img.convert("RGB")
    if "9:16" in target_ratio_name:
        tw, th = 1080, 1920
    else:
        tw, th = 1920, 1080
        
    target_ratio = tw / th
    orig_w, orig_h = img.size
    orig_ratio = orig_w / orig_h

    if orig_ratio > target_ratio:
        # 가로가 긴 경우 세로에 맞춤 [cite: 10]
        nh = th
        nw = int(th * orig_ratio)
    else:
        # 세로가 긴 경우 가로에 맞춤 [cite: 10]
        nw = tw
        nh = int(tw / orig_ratio)

    resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
    
    # 중앙 크롭
    left = (nw - tw) // 2 [cite: 11]
    top = (nh - th) // 2
    return resized.crop((left, top, left + tw, top + th))

# --- [3. 사이드바 설정] ---
with st.sidebar:
    st.markdown("<div style='height: 55px;'></div>", unsafe_allow_html=True)
    
    st.markdown("<p class='sb-label'>⚙️ 목표 프레임 비율</p>", unsafe_allow_html=True)
    target_ratio_name = st.selectbox("RatioSelect", ["9:16 (Shorts)", "16:9 (Wide)"], label_visibility="collapsed")
    
    st.divider()
    st.markdown("<p class='sb-label'>📐 그리드(Grid) 설정</p>", unsafe_allow_html=True)
    col_c, col_r = st.columns(2)
    grid_cols = col_c.number_input("가로 칸 수", 1, 10, 5) [cite: 12]
    grid_rows = col_r.number_input("세로 줄 수", 1, 10, 4)
    
    st.markdown("<p class='sb-label' style='font-size:0.9rem; margin-top:10px;'>최대 추출 개수</p>", unsafe_allow_html=True) [cite: 13]
    max_frames = st.number_input("MaxCount", 1, 100, 20, label_visibility="collapsed")
    
    st.divider()
    
    # 보안 박스
    st.markdown("""
        <div class='security-info'>
            Security Processed<br>
            (Volatile processing in memory)
        </div>
        """, unsafe_allow_html=True)
    st.caption("Kwon_Jeong Edition")

# --- [3.5 생일 축하 서프라이즈 이벤트] --- [cite: 14]
if "celebrated" not in st.session_state:
    st.session_state.celebrated = False

if not st.session_state.celebrated:
    @st.dialog("🎂 Happy Birthday to You! 🎂")
    def birthday_popup():
        st.write("==========================================")
        st.markdown(f"### 🎬 Kwon_Jeong의 Frame Master Pro")
        st.write("### 🎈 2026.4.10 / 08")
        st.markdown("#### **동호회 회원 여러분, 환영합니다!**")
        st.write("==========================================")
        st.write("Jeong 님과 생신을 맞이하신 모든 분들께 진심으로 축하를 전합니다!") [cite: 15]
        
        if st.button("감사합니다! 앱 시작하기 (Enter)", use_container_width=True): [cite: 16]
            st.session_state.celebrated = True
            st.rerun()

    birthday_popup()
    st.stop()

# --- [4. 메인 화면 및 파일 처리] ---
st.markdown("<h1 class='main-title'>Frame Master Pro</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #ffab40; font-size: 1.1rem; font-weight: bold; margin-top: -15px;'>Precision Extraction & Full-Fill Security Engine</p>", unsafe_allow_html=True)
st.markdown("<p class='info-text'>You can achieve as much as you believe you can.</p>", unsafe_allow_html=True)

st.markdown("<p style='color: #ffab40; font-weight: bold; margin-bottom: 5px; margin-top: 25px;'>📂 스토리보드 파일 업로드 (PDF, PNG, JPG)</p>", unsafe_allow_html=True) [cite: 17]
uploaded_file = st.file_uploader("Uploader", type=["pdf", "png", "jpg", "jpeg"], label_visibility="collapsed")

if uploaded_file:
    if uploaded_file.size > MAX_FILE_SIZE:
        st.error("보안 정책상 10MB 이하의 파일만 허용됩니다.")
    else:
        st.success(f"준비 완료: {uploaded_file.name}")
        
        if st.button("🚀 에셋 생성 및 압축 시작"):
            status = st.empty()
            status.write("🏃‍♂️💨 작업을 시작합니다... 🏅🥇") [cite: 18]
            
            zip_buffer = io.BytesIO()
            total_count = 1
            file_ext = uploaded_file.name.split('.')[-1].lower()

            try:
                with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zip_file:
                    # PDF 파일 처리 [cite: 19]
                    if file_ext == 'pdf':
                        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                        for i in range(len(doc)):
                            if total_count > max_frames: break [cite: 20]
                            page = doc.load_page(i)
                            pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))
                            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples) [cite: 21]
                            
                            final_img = transform_frame(img, target_ratio_name)
                            img_io = io.BytesIO() [cite: 22]
                            final_img.save(img_io, format='PNG')
                            zip_file.writestr(f"frame_{total_count:02d}.png", img_io.getvalue())
                            status.write(f"🏃‍♂️ PDF 페이지 {i+1} 처리 완료 🏅")
                            total_count += 1 [cite: 23]
                        doc.close()

                    # 일반 이미지 그리드 처리
                    else:
                        img = Image.open(uploaded_file) [cite: 24]
                        W, H = img.size
                        cw, ch = W // grid_cols, H // grid_rows
                        
                        for r in range(grid_rows): [cite: 26]
                            for c in range(grid_cols):
                                if total_count > max_frames: break
                                
                                left = c * cw [cite: 27]
                                top = r * ch
                                right = min((c + 1) * cw, W) [cite: 28]
                                bottom = min((r + 1) * ch, H)
                                
                                # 프레임 크롭 및 변환 [cite: 29]
                                crop_img = img.crop((left, top, right, bottom))
                                final_img = transform_frame(crop_img, target_ratio_name)
                                
                                # 메모리 내 저장 [cite: 30]
                                img_io = io.BytesIO()
                                final_img.save(img_io, format='PNG') [cite: 31]
                                zip_file.writestr(f"frame_{total_count:02d}.png", img_io.getvalue())
                                
                                status.write(f"🏃‍♂️ 프레임 {total_count} 추출 중... 🏅") [cite: 32]
                                total_count += 1

                # 결과물 다운로드 버튼
                st.download_button(
                    label="📂 추출 에셋 다운로드 (ZIP)", [cite: 33]
                    data=zip_buffer.getvalue(),
                    file_name=f"FrameMaster_Assets.zip",
                    mime="application/zip",
                    use_container_width=True [cite: 34]
                )
                st.balloons()
                status.write("✅ All Mission Accomplished! 🏆") [cite: 35]

            except Exception as e:
                st.error(f"처리 중 오류 발생: {e}")
