# streamlit_app.py
import streamlit as st
import google.generativeai as genai
import os
import re

# Page config
st.set_page_config(
    page_title="AUTO DỊCH TIẾNG TRUNG",
    page_icon="📖",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%);
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-bottom: 30px;
    }
    .stButton>button {
        width: 100%;
        background-color: #4f46e5;
        color: white;
        border-radius: 5px;
        padding: 10px;
        font-weight: bold;
    }
    .success-box {
        padding: 10px;
        background-color: #d1fae5;
        border-left: 4px solid #10b981;
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'genai_model' not in st.session_state:
    st.session_state.genai_model = None
if 'original_content' not in st.session_state:
    st.session_state.original_content = ""
if 'corrected_content' not in st.session_state:
    st.session_state.corrected_content = ""
if 'translated_content' not in st.session_state:
    st.session_state.translated_content = ""

def parse_srt(content):
    """Parse SRT content"""
    blocks = []
    entries = content.strip().split('\n\n')
    
    for entry in entries:
        lines = entry.strip().split('\n')
        if len(lines) >= 3:
            blocks.append({
                'index': lines[0],
                'timestamp': lines[1],
                'text': '\n'.join(lines[2:])
            })
    return blocks

def format_srt(blocks):
    """Format SRT blocks back to string"""
    return '\n\n'.join([
        f"{block['index']}\n{block['timestamp']}\n{block['text']}"
        for block in blocks
    ])

def configure_api(api_key):
    """Configure Gemini API"""
    try:
        genai.configure(api_key=api_key)
        
        models_to_try = [
            'models/gemini-2.0-flash-exp',
            'models/gemini-1.5-flash',
            'gemini-2.0-flash-exp',
            'gemini-1.5-flash',
        ]
        
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                test_response = model.generate_content(
                    "Test",
                    generation_config={'temperature': 0.1, 'max_output_tokens': 5}
                )
                if test_response and test_response.text:
                    st.session_state.genai_model = model
                    return True, model_name
            except:
                continue
        
        return False, "Không tìm thấy model khả dụng"
    except Exception as e:
        return False, str(e)

def correct_chinese(content, style=""):
    """Sửa lỗi tiếng Trung"""
    blocks = parse_srt(content)
    texts_only = '\n===PHÂN_CÁCH===\n'.join([b['text'] for b in blocks])
    
    style_prompt = f"Phong cách: {style}.\n" if style else ""
    
    prompt = f"""Bạn là chuyên gia sửa phụ đề tiếng Trung.

{style_prompt}
Nhiệm vụ:
1. Sửa ngữ pháp, chính tả, dấu câu tiếng Trung
2. Giữ nguyên ý nghĩa
3. Trả về CHÍNH XÁC {len(blocks)} câu
4. Ngăn cách bởi "===PHÂN_CÁCH==="
5. KHÔNG thêm giải thích

Các câu cần sửa:
{texts_only}

Trả về {len(blocks)} câu đã sửa:"""

    response = st.session_state.genai_model.generate_content(prompt)
    result = response.text
    
    corrected_texts = result.split('===PHÂN_CÁCH===')
    corrected_texts = [t.strip() for t in corrected_texts if t.strip()]
    
    while len(corrected_texts) < len(blocks):
        corrected_texts.append(blocks[len(corrected_texts)]['text'])
    corrected_texts = corrected_texts[:len(blocks)]
    
    for i, block in enumerate(blocks):
        block['text'] = corrected_texts[i]
    
    return format_srt(blocks)

def translate_to_vietnamese(content, style=""):
    """Dịch sang tiếng Việt"""
    blocks = parse_srt(content)
    texts_only = '\n===PHÂN_CÁCH===\n'.join([b['text'] for b in blocks])
    
    style_prompt = f"Phong cách dịch: {style}.\n" if style else ""
    
    prompt = f"""Bạn là chuyên gia dịch Trung - Việt.

{style_prompt}
NGUYÊN TẮC DỊCH:
1. ĐỊA DANH - Hán Việt: 上海→Thượng Hải, 北京→Bắc Kinh
2. TÊN NGƯỜI - Hán Việt: 李明→Lý Minh, 王伟→Vương Vỹ
3. Dịch tự nhiên, dễ hiểu

NHIỆM VỤ:
1. Dịch {len(blocks)} câu sang tiếng Việt
2. Ngăn cách bởi "===PHÂN_CÁCH==="
3. KHÔNG thêm giải thích

Các câu cần dịch:
{texts_only}

Trả về {len(blocks)} câu tiếng Việt:"""

    response = st.session_state.genai_model.generate_content(prompt)
    result = response.text
    
    translated_texts = result.split('===PHÂN_CÁCH===')
    translated_texts = [t.strip() for t in translated_texts if t.strip()]
    
    while len(translated_texts) < len(blocks):
        translated_texts.append(blocks[len(translated_texts)]['text'])
    translated_texts = translated_texts[:len(blocks)]
    
    for i, block in enumerate(blocks):
        block['text'] = translated_texts[i]
    
    return format_srt(blocks)

# Header
st.markdown('<div class="main-header"><h1>📖 AUTO DỊCH TIẾNG TRUNG PRO</h1><p>Công cụ dịch phụ đề SRT Trung - Việt tự động</p></div>', unsafe_allow_html=True)

# Sidebar - Cài đặt
with st.sidebar:
    st.header("⚙️ CÀI ĐẶT")
    
    # API Key input
    api_key_input = st.text_input(
        "🔑 Gemini API Key",
        type="password",
        value=st.session_state.api_key,
        help="Lấy API key tại: aistudio.google.com/apikey"
    )
    
    if st.button("💾 Lưu & Kiểm tra API"):
        if api_key_input:
            with st.spinner("Đang kiểm tra API Key..."):
                success, message = configure_api(api_key_input)
                if success:
                    st.session_state.api_key = api_key_input
                    st.success(f"✅ API hợp lệ! Model: {message}")
                else:
                    st.error(f"❌ Lỗi: {message}")
        else:
            st.warning("⚠️ Vui lòng nhập API Key!")
    
    st.markdown("---")
    
    # Style input
    style = st.text_input(
        "🎨 Phong cách (tùy chọn)",
        placeholder="VD: trinh thám, review phim, trang trọng..."
    )
    
    st.markdown("---")
    st.info("💡 **Hướng dẫn:**\n1. Nhập API Key\n2. Tải file SRT\n3. Sửa lỗi\n4. Dịch\n5. Tải xuống")

# Main content
tab1, tab2, tab3 = st.tabs(["📁 Tải File", "✏️ Sửa Lỗi & Dịch", "📊 Kết Quả"])

with tab1:
    st.subheader("📁 Bước 1: Tải File SRT")
    
    uploaded_file = st.file_uploader(
        "Chọn file SRT tiếng Trung",
        type=['srt'],
        help="Chọn file phụ đề SRT cần dịch"
    )
    
    if uploaded_file is not None:
        content = uploaded_file.read().decode('utf-8')
        st.session_state.original_content = content
        
        st.markdown('<div class="success-box">✅ Đã tải file thành công!</div>', unsafe_allow_html=True)
        
        with st.expander("👁️ Xem nội dung gốc"):
            st.text_area("Nội dung file SRT", content, height=300, disabled=True)

with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("✏️ Bước 2: Sửa Lỗi Tiếng Trung")
        
        if st.button("🔄 Sửa Lỗi", disabled=not st.session_state.genai_model or not st.session_state.original_content):
            with st.spinner("Đang sửa lỗi tiếng Trung..."):
                try:
                    corrected = correct_chinese(st.session_state.original_content, style)
                    st.session_state.corrected_content = corrected
                    st.success("✅ Đã sửa lỗi tiếng Trung!")
                except Exception as e:
                    st.error(f"❌ Lỗi: {str(e)}")
        
        if st.session_state.corrected_content:
            st.text_area("📝 Nội dung đã sửa", st.session_state.corrected_content, height=400)
    
    with col2:
        st.subheader("🌐 Bước 3: Dịch Sang Tiếng Việt")
        
        if st.button("🔄 Dịch", disabled=not st.session_state.corrected_content):
            with st.spinner("Đang dịch sang tiếng Việt..."):
                try:
                    translated = translate_to_vietnamese(st.session_state.corrected_content, style)
                    st.session_state.translated_content = translated
                    st.success("✅ Đã dịch sang tiếng Việt!")
                except Exception as e:
                    st.error(f"❌ Lỗi: {str(e)}")
        
        if st.session_state.translated_content:
            # Search & Replace
            with st.expander("🔍 Tìm & Thay Thế"):
                search_col1, search_col2 = st.columns(2)
                with search_col1:
                    search_term = st.text_input("Tìm từ:")
                with search_col2:
                    replace_term = st.text_input("Thay bằng:")
                
                if st.button("🔄 Thay thế tất cả") and search_term and replace_term:
                    st.session_state.translated_content = st.session_state.translated_content.replace(search_term, replace_term)
                    st.success(f"✅ Đã thay thế '{search_term}' → '{replace_term}'")
            
            # Editable text area
            edited_translation = st.text_area(
                "📝 Bản dịch (có thể chỉnh sửa)", 
                st.session_state.translated_content, 
                height=400
            )
            st.session_state.translated_content = edited_translation

with tab3:
    st.subheader("💾 Bước 4: Tải Xuống Kết Quả")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.session_state.original_content:
            st.download_button(
                label="📥 Tải File Gốc",
                data=st.session_state.original_content,
                file_name="original.srt",
                mime="text/plain"
            )
    
    with col2:
        if st.session_state.corrected_content:
            st.download_button(
                label="📥 Tải Bản Đã Sửa",
                data=st.session_state.corrected_content,
                file_name="corrected_chinese.srt",
                mime="text/plain"
            )
    
    with col3:
        if st.session_state.translated_content:
            st.download_button(
                label="📥 Tải Bản Dịch Việt",
                data=st.session_state.translated_content,
                file_name="translated_vietnamese.srt",
                mime="text/plain"
            )
    
    # Display results
    if st.session_state.translated_content:
        st.markdown("---")
        st.subheader("📊 So Sánh Kết Quả")
        
        result_col1, result_col2 = st.columns(2)
        
        with result_col1:
            st.markdown("**🇨🇳 Tiếng Trung (Đã sửa)**")
            st.text_area("", st.session_state.corrected_content, height=400, disabled=True, key="result_chinese")
        
        with result_col2:
            st.markdown("**🇻🇳 Tiếng Việt**")
            st.text_area("", st.session_state.translated_content, height=400, disabled=True, key="result_vietnamese")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "Made with ❤️ | Powered by Google Gemini AI"
    "</div>",
    unsafe_allow_html=True
)