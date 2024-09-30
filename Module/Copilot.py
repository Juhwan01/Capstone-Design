import streamlit as st
from openai import OpenAI
import os
import docker
import tempfile
import subprocess
import re

# Streamlit 페이지 설정
st.set_page_config(page_title="Multi-Language Code Editor", layout="wide")

class MultiLanguageCopilot:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.assistant = None
        self.thread = None
        self.docker_client = docker.from_env()

    def create_assistant(self):
        self.assistant = self.client.beta.assistants.create(
            name="Multi-Language Copilot",
            instructions="You are a helpful programming assistant capable of working with multiple programming languages. Provide code suggestions, explanations, and help with debugging.",
            model="gpt-4-1106-preview",
            tools=[{"type": "code_interpreter"}]
        )

    def create_thread(self):
        self.thread = self.client.beta.threads.create()

    def ask_question(self, question: str) -> str:
        if not self.assistant or not self.thread:
            raise ValueError("Assistant or Thread not initialized")

        message = self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role="user",
            content=question
        )

        run = self.client.beta.threads.runs.create(
            thread_id=self.thread.id,
            assistant_id=self.assistant.id
        )

        while run.status != "completed":
            run = self.client.beta.threads.runs.retrieve(thread_id=self.thread.id, run_id=run.id)

        messages = self.client.beta.threads.messages.list(thread_id=self.thread.id)
        return messages.data[0].content[0].text.value

    def execute_code(self, code: str, language: str, user_inputs: list) -> str:
        language_configs = {
            'python': {'image': 'python:3.9-slim', 'file_ext': '.py', 'cmd': ['python']},
            'java': {'image': 'openjdk:11', 'file_ext': '.java', 'cmd': ['java']},
            'c': {'image': 'gcc:latest', 'file_ext': '.c', 'cmd': ['gcc', '-o', '/code/out']},
            'c++': {'image': 'gcc:latest', 'file_ext': '.cpp', 'cmd': ['g++', '-o', '/code/out']},
            'c#': {'image': 'mcr.microsoft.com/dotnet/sdk:5.0', 'file_ext': '.cs', 'cmd': ['dotnet', 'run']},
            'javascript': {'image': 'node:14', 'file_ext': '.js', 'cmd': ['node']},
        }

        if language.lower() not in language_configs:
            return f"Error: Unsupported language {language}"

        config = language_configs[language.lower()]
        
        # 수정된 코드 생성
        modified_code = self.modify_code_for_input(code, language, user_inputs)

        with tempfile.NamedTemporaryFile(mode='w+', suffix=config['file_ext'], delete=False) as temp_file:
            temp_file.write(modified_code)
            temp_file_path = temp_file.name

        try:
            compile_cmd = []
            if language.lower() == 'java':
                class_name = self.extract_java_class_name(modified_code)
                compile_cmd = ['javac', f'/code/{os.path.basename(temp_file_path)}']
                run_cmd = ['java', '-cp', '/code', class_name]
            elif language.lower() in ['c', 'c++']:
                compile_cmd = config['cmd'] + [f'/code/{os.path.basename(temp_file_path)}']
                run_cmd = ['/code/out']
            elif language.lower() == 'c#':
                compile_cmd = ['dotnet', 'build', f'/code/{os.path.basename(temp_file_path)}']
                run_cmd = ['dotnet', 'run', '--no-build', f'/code/{os.path.basename(temp_file_path)}']
            else:
                run_cmd = config['cmd'] + [f'/code/{os.path.basename(temp_file_path)}']

            # Run the code in Docker
            container = self.docker_client.containers.run(
                config['image'],
                command=['sh', '-c', f'cd /code && {" && ".join([" ".join(cmd) for cmd in [compile_cmd, run_cmd] if cmd])}'],
                volumes={os.path.dirname(temp_file_path): {'bind': '/code', 'mode': 'rw'}},
                working_dir='/code',
                detach=True
            )

            # Wait for the container to finish and get the output
            container.wait(timeout=10)
            output = container.logs().decode('utf-8')

            # Clean up
            container.remove()

            return output

        except Exception as e:
            return f"Error: {str(e)}"
        finally:
            os.unlink(temp_file_path)

    def modify_code_for_input(self, code: str, language: str, user_inputs: list) -> str:
        if language.lower() == 'python':
            lines = code.split('\n')
            modified_lines = []
            input_count = 0
            for line in lines:
                if 'input(' in line:
                    prompt = line.split('input(')[1].split(')')[0]
                    modified_lines.append(f"print({prompt})")
                    if input_count < len(user_inputs):
                        modified_lines.append(f"_input_{input_count} = '{user_inputs[input_count]}'")
                        modified_lines.append(f"print(_input_{input_count})")
                        modified_lines.append(line.replace('input(', f'_input_{input_count} or input('))
                    else:
                        modified_lines.append(line)
                    input_count += 1
                else:
                    modified_lines.append(line)
            return '\n'.join(modified_lines)
        # 다른 언어에 대한 처리도 추가할 수 있습니다.
        return code

    def extract_java_class_name(self, code):
        for line in code.split('\n'):
            if 'class' in line:
                return line.split('class')[1].strip().split()[0]
        return 'Main'  # Default to Main if no class name found

    def check_input_needed(self, code: str, language: str) -> int:
        if language.lower() == 'python':
            return code.count('input(')
        # 다른 언어에 대한 처리도 추가할 수 있습니다.
        return 0

def main():
    st.title("Multi-Language Code Editor")

    if 'copilot' not in st.session_state:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            st.error("OPENAI_API_KEY environment variable not set")
            return

        st.session_state.copilot = MultiLanguageCopilot(api_key)
        st.session_state.copilot.create_assistant()
        st.session_state.copilot.create_thread()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Code Editor")
        language = st.selectbox("Select Language", ["Python", "Java", "C", "C++", "C#", "JavaScript"])
        code = st.text_area("Enter your code here:", height=300)

        col1_1, col1_2 = st.columns(2)
        with col1_1:
            if st.button("Get Suggestions"):
                if code:
                    with st.spinner("Generating suggestions..."):
                        suggestion = st.session_state.copilot.ask_question(f"Provide suggestions or improvements for this {language} code:\n\n{code}")
                    st.session_state.suggestion = suggestion
                else:
                    st.warning("Please enter some code first.")

        with col1_2:
            if code:
                input_count = st.session_state.copilot.check_input_needed(code, language)
                user_inputs = []
                if input_count > 0:
                    st.write(f"This code requires {input_count} input(s). Please provide the inputs below:")
                    for i in range(input_count):
                        user_input = st.text_input(f"Input {i+1}:")
                        user_inputs.append(user_input)
                
                if st.button("Execute Code"):
                    with st.spinner("Executing code..."):
                        output = st.session_state.copilot.execute_code(code, language, user_inputs)
                    st.session_state.execution_output = output
            else:
                st.warning("Please enter some code first.")

    with col2:
        st.subheader("Copilot Suggestions")
        if 'suggestion' in st.session_state:
            st.write(st.session_state.suggestion)
        else:
            st.write("Copilot suggestions will appear here.")

        st.subheader("Code Execution Output")
        if 'execution_output' in st.session_state:
            st.code(st.session_state.execution_output)
        else:
            st.write("Code execution output will appear here.")

    st.subheader("Ask Copilot")
    user_question = st.text_input("Ask a programming question:")
    if st.button("Get Answer"):
        if user_question:
            with st.spinner("Generating answer..."):
                answer = st.session_state.copilot.ask_question(user_question)
            st.write("Copilot's Answer:")
            st.write(answer)
        else:
            st.warning("Please enter a question first.")

if __name__ == "__main__":
    main()