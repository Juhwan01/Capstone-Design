from pydantic import BaseModel

    
class CodeComparison(BaseModel):
    original_code: str
    new_code: str

class GPTRequest(BaseModel):
    code: str
    current_code: str = ""  # 현재 에디터의 코드
    question: str = ""
    type: str = "simple"
    chat_history: list = []