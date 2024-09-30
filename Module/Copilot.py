import streamlit as st
from openai import OpenAI
import os
import sys
import io
import contextlib
import ast

class SimpleCopilot:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.assistant = None
        self.thread = None

    def create_assistant(self):
        self.assistant = self.client.beta.assistants.create(
            name="Simple Copilot",
            instructions="You are a helpful programming assistant. Provide code suggestions, explanations, and help with debugging.",
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

def is_safe_code(code: str) -> bool:
    """Check if the code is safe to execute."""
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                return False  # Disallow any imports
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr in ['open', 'exec', 'eval']:
                    return False  # Disallow file operations and dynamic code execution
    except SyntaxError:
        return False
    return True

def execute_code(code: str) -> str:
    """Execute the given code and return the output."""
    if not is_safe_code(code):
        return "Error: This code contains potentially unsafe operations and cannot be executed."

    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    
    try:
        exec(code)
        sys.stdout = old_stdout
        return redirected_output.getvalue()
    except Exception as e:
        sys.stdout = old_stdout
        return f"Error: {str(e)}"

def main():
    st.set_page_config(page_title="Copilot Code Editor", layout="wide")
    st.title("Copilot Code Editor")

    if 'copilot' not in st.session_state:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            st.error("OPENAI_API_KEY environment variable not set")
            return

        st.session_state.copilot = SimpleCopilot(api_key)
        st.session_state.copilot.create_assistant()
        st.session_state.copilot.create_thread()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Code Editor")
        code = st.text_area("Enter your code here:", height=300)

        col1_1, col1_2 = st.columns(2)
        with col1_1:
            if st.button("Get Suggestions"):
                if code:
                    with st.spinner("Generating suggestions..."):
                        suggestion = st.session_state.copilot.ask_question(f"Provide suggestions or improvements for this code:\n\n{code}")
                    st.session_state.suggestion = suggestion
                else:
                    st.warning("Please enter some code first.")

        with col1_2:
            if st.button("Execute Code"):
                if code:
                    output = execute_code(code)
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