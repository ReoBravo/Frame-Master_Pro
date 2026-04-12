import streamlit as st
from PIL import Image
import io
import zipfile
import fitz  # PyMuPDF

# --- [1. 보안 및 페이지 설정] ---
st.set_page_config(page_title="Frame Master Pro", layout="wide")

# 보안을 위한 최대 파일 용량 제한 (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024 

# 디자인 설정: 밝은 파랑 사이드바 및 레이아웃 정렬
st.markdown("""
    <style>
    /* 메인 배경색 (하늘색) */
    .main { background-color: #e3f2fd; color: #333333; }
    .stApp { background-color: #e3f2fd; }
    
    /* 사이드바 바탕색 (밝은 파랑) */
    [data-testid="stSidebar"] { background-color: #64b5f6; color: #ffffff; }
    
    /* 보안 박스 (슬림한 디자인) */
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
    
    /* 사이드바 내부 텍스트 */
    .sb-label { color: #ffffff !important; font-weight: bold; font-size: 1.0rem; margin-bottom: 5px; }
    
    /* 버튼 스타일 */
    .stButton>button {
        background: linear-gradient(90deg, #1e88e5 0%, #42a5f5 100%);
        color: white; border: none; border-radius: 10px;
        padding: 0.5rem 2rem; font-weight: bold; width: 100%;
    }
    
    /* 메인 타이틀 및 텍스트 */
    .main-title { color: #1a237e; font-family: 'Inter', sans-serif; font-weight: 800; font-size: 3.5rem; margin-top: -45px; }
    .info-text { color: #555555; font-size: 0.85rem; margin-top: -15px; font-style: italic; }
    
    /* 사이드바 폰트 색상 강제 */
    [data-testid="stSidebar"] .stMarkdown p { color: #ffffff !important; }
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
        # 가로가 긴 경우 세로에 맞춤
        nh = th
        nw = int(th * orig_ratio)
    else:
        # 세로가 긴 경우 가로에 맞춤
        nw = tw
        nh = int(tw / orig_ratio)

    resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
    
    # 중앙 크롭
    left = (nw - tw) // 2
    top = (nh - th) // 2
    return resized.crop((left, top, left + tw, top + th))

# --- [3. 사이드바 설정] ---
with st.sidebar:
    # 메인 타이틀 라인과 높이 맞춤용 여백
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
    
    # 보안 박스 (슬림 버전)
    st.markdown("""
        <div class='security-info'>
            Security Processed<br>
            (Volatile processing in memory)
        </div>
        """, unsafe_allow_html=True)
    st.caption("Kwon_Jeong Edition")

# --- [4. 메인 화면 및 파일 처리] ---
st.markdown("<h1 class='main-title'>Frame Master Pro</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #ffab40; font-size: 1.1rem; font-weight: bold; margin-top: -15px;'>Precision Extraction & Full-Fill Security Engine</p>", unsafe_allow_html=True)
st.markdown("<p class='info-text'>You can achieve as much as you believe you can.</p>", unsafe_allow_html=True)

st.markdown("<p style='color: #ffab40; font-weight: bold; margin-bottom: 5px; margin-top: 25px;'>📂 스토리보드 파일 업로드 (PDF, PNG, JPG)</p>", unsafe_allow_html=True)
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
                    # PDF 파일 처리
                    if file_ext == 'pdf':
                        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                        for i in range(len(doc)):
                            if total_count > max_frames: break
                            page = doc.load_page(i)
                            pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))
                            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                            
                            final_img = transform_frame(img, target_ratio_name)
                            img_io = io.BytesIO()
                            final_img.save(img_io, format='PNG')
                            zip_file.writestr(f"frame_{total_count:02d}.png", img_io.getvalue())
                            status.write(f"🏃‍♂️ PDF 페이지 {i+1} 처리 완료 🏅")
                            total_count += 1
                        doc.close()

                    # 일반 이미지 그리드 처리
                    else:
                        img = Image.open(uploaded_file)
                        W, H = img.size
                        cw, ch = W // grid_cols, H // grid_rows
                        
                        # 이 부분이 아까 생략되었던 핵심 루프입니다!
                        for r in range(grid_rows):
                            for c in range(grid_cols):
                                if total_count > max_frames: break
                                
                                left = c * cw
                                top = r * ch
                                right = min((c + 1) * cw, W)
                                bottom = min((r + 1) * ch, H)
                                
                                # 프레임 크롭 및 변환
                                crop_img = img.crop((left, top, right, bottom))
                                final_img = transform_frame(crop_img, target_ratio_name)
                                
                                # 메모리 내 저장
                                img_io = io.BytesIO()
                                final_img.save(img_io, format='PNG')
                                zip_file.writestr(f"frame_{total_count:02d}.png", img_io.getvalue())
                                
                                status.write(f"🏃‍♂️ 프레임 {total_count} 추출 중... 🏅")
                                total_count += 1

                # 결과물 다운로드 버튼
                st.download_button(
                    label="📂 추출 에셋 다운로드 (ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name=f"FrameMaster_Assets.zip",
                    mime="application/zip",
                    use_container_width=True
                )
                st.balloons()
                status.write("✅ All Mission Accomplished! 🏆")

            except Exception as e:
                st.error(f"처리 중 오류 발생: {e}")