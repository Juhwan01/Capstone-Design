import streamlit as st
import os
from langchain_core.output_parsers import StrOutputParser
from langchain_huggingface import HuggingFaceEndpoint
from langchain_experimental.utilities import PythonREPL
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough

# StarCoder2 모델 설정
starcoder_llm = HuggingFaceEndpoint(
    repo_id="bigcode/starcoder2-15b",
    max_new_tokens=256,
    temperature=0.1,
    huggingfacehub_api_token=os.environ["HUGGINGFACEHUB_API_TOKEN"],
)

# GPT-4 모델 설정
gpt4_llm = ChatOpenAI(temperature=0, model_name="gpt-4o-2024-08-06")

# 프롬프트 템플릿 설정
code_generation_prompt = PromptTemplate.from_template(
    "다음 Python 코드를 작성해주세요. 코드만 반환하고 추가 설명은 하지 마세요: {task}"
)

code_completion_prompt = PromptTemplate.from_template(
    "다음 Python 코드를 완성해주세요. '#' 표시 이후의 내용은 무시하고, '#' 이전의 코드만을 기반으로 전체 함수를 완성하여 반환하세요. 추가 설명은 하지 마세요:\n{code}"
)

chatbot_prompt = PromptTemplate.from_template(
    "당신은 Python 프로그래밍 조수입니다. 다음 질문에 대해 간결하고 정확하게 답변해주세요: {question}"
)

# 코드 생성 체인
code_chain = (
    {"task": RunnablePassthrough()} 
    | code_generation_prompt 
    | starcoder_llm 
    | StrOutputParser()
)

# 코드 완성 체인
code_completion_chain = (
    {"code": RunnablePassthrough()}
    | code_completion_prompt
    | starcoder_llm
    | StrOutputParser()
)

# 챗봇 체인
chatbot_chain = (
    {"question": RunnablePassthrough()}
    | chatbot_prompt
    | gpt4_llm
    | StrOutputParser()
)

# Python 실행 함수
python_repl = PythonREPL()

def execute_python(code):
    try:
        return python_repl.run(code)
    except Exception as e:
        return f"실행 오류: {str(e)}"

# Streamlit 앱
st.title("Python Copilot")

# 탭 생성
tab1, tab2, tab3 = st.tabs(["코드 생성", "코드 자동완성", "Python 챗봇"])

with tab1:
    st.header("코드 생성")
    task = st.text_input("어떤 Python 코드를 생성할까요?")
    if st.button("코드 생성"):
        with st.spinner("코드 생성 중..."):
            try:
                generated_code = code_chain.invoke(task)
                st.code(generated_code, language="python")
                if st.button("코드 실행"):
                    with st.spinner("코드 실행 중..."):
                        result = execute_python(generated_code)
                    st.write("실행 결과:")
                    st.write(result)
            except Exception as e:
                st.error(f"코드 생성 중 오류 발생: {str(e)}")

with tab2:
    st.header("코드 자동완성")
    code_input = st.text_area("코드를 입력하세요 (자동완성을 원하는 부분은 '#'로 표시):", height=200)
    if st.button("자동완성"):
        with st.spinner("코드 완성 중..."):
            try:
                # '#' 이전의 코드만 추출
                code_to_complete = code_input.split('#')[0].strip()
                completed_code = code_completion_chain.invoke(code_to_complete)
                st.code(completed_code, language="python")
            except Exception as e:
                st.error(f"코드 완성 중 오류 발생: {str(e)}")

with tab3:
    st.header("Python 챗봇")
    question = st.text_input("Python에 관해 무엇이든 물어보세요:")
    if st.button("질문하기"):
        with st.spinner("답변 생성 중..."):
            try:
                answer = chatbot_chain.invoke(question)
                st.write("답변:")
                st.write(answer)
            except Exception as e:
                st.error(f"답변 생성 중 오류 발생: {str(e)}")

# 사이드바에 사용 설명 추가
st.sidebar.title("사용 방법")
st.sidebar.write("""
1. 코드 생성: 원하는 Python 코드에 대한 설명을 입력하세요.
2. 코드 자동완성: 코드의 일부를 입력하고 '#'으로 완성할 부분을 표시하세요. '#' 이후의 내용은 무시됩니다.
3. Python 챗봇: Python 관련 질문을 자유롭게 물어보세요.
""")