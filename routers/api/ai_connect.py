from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
import os
from domains.ai.dto import *
import openai
from dotenv import load_dotenv
from difflib import SequenceMatcher

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
        # 원드 정리: 빈 줄 제거 및 공백 정규화
        def clean_code(code):
            lines = [line.strip() for line in code.splitlines() if line.strip()]
            return lines

        original_lines = clean_code(comparison.original_code)
        new_lines = clean_code(comparison.new_code)
        
        changes = {
            "additions": [],
            "deletions": [],
            "modifications": []
        }
        
        # styled-components 스타일 블록 분석
        def parse_style_block(lines):
            styles = {}
            current_selector = None
            
            for line in lines:
                if '`' in line:  # 스타일 블록 시작/끝
                    continue
                    
                line = line.strip()
                if not line:
                    continue
                    
                if line.endswith('{'):  # 새로운 선택자 시작
                    current_selector = line[:-1].strip()
                    styles[current_selector] = []
                elif line.endswith('}'):  # 선택자 블록 끝
                    current_selector = None
                elif current_selector and ':' in line:  # 스타일 속성
                    styles[current_selector].append(line)
            
            return styles
        
        original_styles = parse_style_block(original_lines)
        new_styles = parse_style_block(new_lines)
        
        # 스타일 변경사항 분석
        for selector, new_props in new_styles.items():
            if selector in original_styles:
                # 기존 스타일에 새로운 속성 추가 또는 수정
                original_props = set(original_styles[selector])
                new_props_set = set(new_props)
                
                added_props = new_props_set - original_props
                if added_props:
                    changes["additions"].extend({
                        "line": -1,  # 실제 라인 번호는 프론트엔드에서 결정
                        "content": prop
                    } for prop in added_props)
                
                modified_props = {prop for prop in new_props if prop not in added_props}
                if modified_props:
                    changes["modifications"].extend({
                        "original_line": -1,
                        "new_line": -1,
                        "original_content": "",
                        "new_content": prop
                    } for prop in modified_props)
            else:
                # 새로운 스타일 블록 추가
                changes["additions"].append({
                    "line": -1,
                    "content": f"{selector} {{\n  " + "\n  ".join(new_props) + "\n}}"
                })
        
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
        # 파일이 비어있거나 선택되지 않은 경우
        if not request.code or request.code.isspace():
            if not request.question:
                return {"answer": "파일을 선택하거나 프로그래밍 관련 질문을 입력해주세요."}
            
            # GPT에게 일반적인 프로그래밍 질문 전달
            system_prompt = """당신은 프로그래밍 전문가입니다.
            JavaScript와 Python에 대한 질문에만 답변해주세요.
            다른 주제의 질문이 들어오면 "JavaScript 또는 Python 관련 질문만 답변 가능합니다."라고 답변해주세요.
            코드 예제가 필요한 경우 실행 가능한 코드를 제공해주세요.
            답변은 다음 형식으로 제공해주세요:
            1. 개념 설명
            2. 코드 예제 (있는 경우)
            3. 추가 참고사항"""

            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": request.question}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            return {"answer": response.choices[0].message.content}

        # 파일 분석 로직
        file_extension = request.code.split('.')[-1].lower() if '.' in request.code else ''
        
        if file_extension not in ['js', 'py']:
            return {"answer": "지원하지 않는 파일 형식입니다. JavaScript 또는 Python 파일만 분석 가능합니다."}

        system_prompt = f"""당신은 {file_extension.upper()} 코드 분석 전문가입니다. 
        주어진 코드 파일의 컨텍스트를 기반으로만 질문에 답변해주세요. 
        코드의 구조, 목적, 기능을 정확히 이해하고 설명해주세요.
        답변은 다음 형식으로 제공해주세요:
        1. 코드 분석 결과
        2. 질문에 대한 답변
        3. 개선 제안사항 (있는 경우)"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"코드:\n{request.code}\n\n질문:\n{request.question}"}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        return {"answer": response.choices[0].message.content}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))