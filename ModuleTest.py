from openai import OpenAI
import time
from dataclasses import dataclass

client = OpenAI(api_key='')

@dataclass
class CodeResponse:
    code_output: str
    explanation: str
    suggested_code: str = ""
    input_required: str = ""

assistant = client.beta.assistants.create(
    name="Multi-Language Coding Assistant",
    instructions="""You are a helpful coding assistant capable of working with multiple programming languages. Execute code in the specified language and provide explanations. 
    If the code requires user input, clearly state what inputs are needed.
    Always format your response exactly as follows, including the labels:

    CODE OUTPUT:
    <Provide the exact output of the code execution here, or state that input is required if applicable. If there's no output, write 'No output'.>

    EXPLANATION:
    <Provide your explanation of the code, its execution, or why input is required.>

    SUGGESTED CODE:
    <If there was an error or if input handling can be improved, provide the complete corrected or improved code here. Ensure the entire code is included, not just comments or partial code.>

    INPUT REQUIRED:
    <If the code requires user input, list the required inputs here, one per line. If no input is required, write 'None'.>

    Ensure that you always include all four sections, even if some are empty. Do not include any other text or formatting in your response. When executing suggested code, use the provided inputs if any.""",
    tools=[{"type": "code_interpreter"}],
    model="gpt-4o-mini-2024-07-18"
)

def parse_response(response_text: str) -> CodeResponse:
    sections = response_text.split("\n\n")
    response = CodeResponse("", "", "", "")
    
    current_section = ""
    for line in response_text.split("\n"):
        if line.startswith("CODE OUTPUT:"):
            current_section = "code_output"
            continue
        elif line.startswith("EXPLANATION:"):
            current_section = "explanation"
            continue
        elif line.startswith("SUGGESTED CODE:"):
            current_section = "suggested_code"
            continue
        elif line.startswith("INPUT REQUIRED:"):
            current_section = "input_required"
            continue

        if current_section == "code_output":
            response.code_output += line + "\n"
        elif current_section == "explanation":
            response.explanation += line + "\n"
        elif current_section == "suggested_code":
            response.suggested_code += line + "\n"
        elif current_section == "input_required":
            response.input_required += line + "\n"

    # Trim whitespace and remove ```python and ``` from suggested code
    response.code_output = response.code_output.strip()
    response.explanation = response.explanation.strip()
    response.suggested_code = response.suggested_code.strip().replace("```python", "").replace("```", "").strip()
    response.input_required = response.input_required.strip()

    if response.input_required == "None":
        response.input_required = ""

    return response

def run_conversation(language: str, user_input: str, provided_inputs: str = "") -> CodeResponse:
    thread = client.beta.threads.create()
    content = f"Language: {language}\nCode: {user_input}"
    if provided_inputs:
        content += f"\nProvided Inputs: {provided_inputs}"
    
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=content
    )
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )

    while True:
        run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if run_status.status == 'completed':
            break
        elif run_status.status == 'failed':
            return CodeResponse("Run failed", "The assistant encountered an error while processing the request.")
        time.sleep(1)

    messages = client.beta.threads.messages.list(thread_id=thread.id)
    assistant_messages = [msg for msg in messages if msg.role == 'assistant']
    
    if assistant_messages:\
        response_text = assistant_messages[0].content[0].text.value
        print("Raw assistant response:", response_text)  # 디버깅을 위해 원본 응답 출력
        return parse_response(response_text)
    else:
        return CodeResponse("No response", "The assistant did not provide a response")

def get_user_inputs(required_inputs: str) -> str:
    inputs = []
    for input_desc in required_inputs.split('\n'):
        user_input = input(f"{input_desc.strip()}: ")
        inputs.append(user_input)
    return "|".join(inputs)

def interactive_coding_session():
    print("Welcome to the Multi-Language Coding Assistant!")
    language = input("Enter the programming language you want to use: ")
    
    while True:
        with open('test.py', 'r', encoding='utf-8') as file:
            user_input = file.read()
        
        response = run_conversation(language, user_input)
        
        if response.suggested_code:
            print("\nThe original code has some issues. Here's the suggested fix:")
            print(response.suggested_code)
            user_choice = input("Do you want to run the suggested code? (yes/no): ")
            if user_choice.lower() == 'yes':
                if response.input_required:
                    print("\nThis code requires user input.")
                    provided_inputs = get_user_inputs(response.input_required)
                    response = run_conversation(language, response.suggested_code, provided_inputs)
                else:
                    response = run_conversation(language, response.suggested_code)
        
        print("\nCode Output:")
        print(response.code_output)
        print("\nExplanation:")
        print(response.explanation)
        break
            

if __name__ == "__main__":
    interactive_coding_session()