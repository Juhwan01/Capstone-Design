import streamlit as st
import requests
import re

API_URL = "https://api-inference.huggingface.co/models/bigcode/starcoder2-15b"
headers = {"Authorization": "Bearer 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"}

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

def remove_comments(code):
    # 주석 제거 (# 으로 시작하는 줄 전체를 제거)
    return re.sub(r'^\s*#.*$', '', code, flags=re.MULTILINE).strip()

def truncate_at_plus(code):
    # # + 이후의 코드를 제거
    parts = code.split('# +', 1)
    return parts[0].strip()

st.title("코드 자동 완성 데모 (# + 이후 제외)")

# session_state를 사용하여 입력 상태 유지
if 'user_input' not in st.session_state:
    st.session_state.user_input = ""

# 텍스트 영역 위젯 생성
user_input = st.text_area("코드를 입력하세요:", value=st.session_state.user_input, height=400)

if st.button("자동 완성"):
    if user_input:
        with st.spinner("코드 생성 중..."):
            output = query({
                "inputs": user_input,
            })
            
            if isinstance(output, list) and len(output) > 0 and 'generated_text' in output[0]:
                completed_code = output[0]['generated_text']
                truncated_code = truncate_at_plus(completed_code)
                code_without_comments = remove_comments(truncated_code)
                
                # 세션 상태 업데이트
                st.session_state.user_input = code_without_comments
                
                # 입력칸 새로고침을 위한 rerun
                st.rerun()  # 여기를 수정했습니다
            else:
                st.error("API 응답 형식이 예상과 다릅니다. 다시 시도해주세요.")
    else:
        st.warning("코드를 입력해주세요.")

st.markdown("---")
st.markdown("이 데모는 Hugging Face의 Starcoder2-15b 모델을 사용합니다. 생성된 코드에서 주석을 제거하고, '# +' 이후의 코드를 제외한 후 입력칸에 표시합니다.")