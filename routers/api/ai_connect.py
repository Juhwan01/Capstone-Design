from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
import os
from domains.ai.dto import *
import openai
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(tags=["ai"])

# OpenAI API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")
print(f"OpenAI API 키 설정됨: {'Yes' if openai.api_key else 'No'}")
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")

@router.post("/api/analyze-code-changes")
async def analyze_code_changes(comparison: CodeComparison):
    try:
        # 원본 코드와 새 코드를 라인 단위로 분리
        original_lines = comparison.original_code.splitlines()
        new_lines = comparison.new_code.splitlines()
        
        # 변경사항 분석
        changes = {
            "additions": [],
            "deletions": [],
            "modifications": []
        }
        
        # 간단한 diff 알고리즘 구현
        from difflib import SequenceMatcher
        matcher = SequenceMatcher(None, original_lines, new_lines)
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'insert':
                changes["additions"].extend({
                    "line": j,
                    "content": new_lines[j]
                } for j in range(j1, j2))
            elif tag == 'delete':
                changes["deletions"].extend({
                    "line": i,
                    "content": original_lines[i]
                } for i in range(i1, i2))
            elif tag == 'replace':
                changes["modifications"].extend({
                    "original_line": i,
                    "new_line": j,
                    "original_content": original_lines[i],
                    "new_content": new_lines[j]
                } for i, j in zip(range(i1, i2), range(j1, j2)))
        
        return {
            "status": "success",
            "changes": changes
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



@router.post("/api/gpt-4o-mini")
async def process_gpt4o_mini(request: GPTRequest):
    try:
        if not openai.api_key:
            return {"answer": "OpenAI API 키가 설정되지 않았습니다."}

        client = openai.OpenAI()
        
        # 시스템 프롬프트 수정
        system_content = """당신은 프로그래밍과 IT 기술 분야의 전문가입니다. 
        다른 분야에 대한 질문은 절대 답변하지 마세요.
        모든 프로그래밍 언어에 대한 질문에 답변할 수 있으며, 
        사용자가 특정 언어로 코드 변환을 요청할 경우 해당 언어로 변환하여 제공해주세요.
        이전 코드의 기능을 동일하게 유지하면서 요청한 언어로 변환해주세요."""

        messages = [
            {
                "role": "system",
                "content": system_content
            }
        ]

        # 이전 대화 내용에서 언어 변환 요청 확인
        target_language = None
        if request.question.lower().find("python") >= 0:
            target_language = "python"
        elif request.question.lower().find("javascript") >= 0:
            target_language = "javascript"
        # 필요한 다른 언어들도 추가 가능

        # 이전 대화 내용 추가
        for chat in request.chat_history:
            messages.append({
                "role": "user" if chat.get("isUser") else "assistant",
                "content": chat.get("text", "")
            })

        # 현재 질문에 언어 컨텍스트 추가
        if request.type == "simple":
            if request.code.strip():
                current_prompt = f"""
다음 코드와 질문을 확인하고 답변해주세요:

코드:
{request.code}

질문:
{request.question}

{f'이 코드를 {target_language}로 변환해주세요.' if target_language else ''}
"""
            else:
                current_prompt = request.question

            messages.append({"role": "user", "content": current_prompt})

            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1000
                )
                
                answer = response.choices[0].message.content
                return {"answer": answer}
                
            except Exception as e:
                return {"answer": f"OpenAI API 오류: {str(e)}"}

        # optimize와 detailed 타입은 코드가 필수
        if not request.code:
            return {"answer": "코드를 입력해주세요."}

        try:
            if request.type == "optimize":
                prompt = f"""
다음 코드를 분석하고 최적화된 버전을 제안해주세요.
현재 코드와의 호환성을 고려하여 변경사항을 제안해주세요.

현재 코드:
{request.current_code}

최적화할 코드:
{request.code}

다음 형식으로 응답해주세요:
1. 변경사항 요약
2. 최적화된 코드 (```로 감싸서)
3. 각 변경사항에 대한 설명
"""
            else:  # detailed
                prompt = f"""
다음 코드를 자세히 분석하고 설명해주세요:

{request.code}

다음 항목들을 포함해서 설명해주세요:
1. 코드의 전반적인 목적과 주요 기능
2. 최적화된 부분들의 상세 설명
3. 성능 개선 포인트
4. 코드 가독성 향상 부분
5. 잠재적인 버그 예방 요소
6. 사용된 최신 문법이나 패턴
7. 추가 개선 가능성
"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 코드를 분석하고 설명하는 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content
            return {"answer": answer}
            
        except Exception as e:
            return {"answer": f"OpenAI API 오류: {str(e)}"}
            
    except Exception as e:
        return {"answer": f"서버 오류: {str(e)}"}

@router.post("/api/analyze-file")
async def analyze_file(request: GPTRequest):
    try:
        # 파일 확장자 추출
        file_extension = request.code.split('.')[-1].lower() if '.' in request.code else ''
        
        # 지원하는 파일 확장자 확인
        if file_extension not in ['js', 'py']:
            return {"answer": "지원하지 않는 파일 형식입니다. JavaScript 또는 Python 파일만 분석 가능합니다."}

        # 시스템 프롬프트 설정
        system_prompt = f"""당신은 {file_extension.upper()} 코드 분석 전문가입니다. 
주어진 코드 파일의 컨텍스트를 기반으로 질문에 답변해주세요. 
코드의 구조, 목적, 기능을 정확히 이해하고 설명해주세요."""

        # 사용자 프롬프트 구성
        user_prompt = f"""다음 {file_extension.upper()} 코드 파일을 분석하고 질문에 답변해주세요.

코드 파일:
{request.code}

질문:
{request.question}

다음 형식으로 답변해주세요:
1. 코드 관련 설명
2. 질문에 대한 답변
3. 관련 예시나 추가 설명 (필요한 경우)
"""

        # GPT API 호출
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        answer = response.choices[0].message.content
        return {"answer": answer}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))