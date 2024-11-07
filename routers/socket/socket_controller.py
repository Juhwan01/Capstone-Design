from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import openai, os
from dependencies.config import get_config

config = get_config()


router = APIRouter(prefix='/socket',tags=["Socket"])

# WebSocket 핸들러
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # 클라이언트로부터 메시지 수신
            data = await websocket.receive_text()
            data = eval(data)
            print("코드 변경 감지:", data)

            completion = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "코드 자동 완성 도우미입니다. 사용자의 코드를 분석하여 적절한 언어로 코드를 제안합니다.\n" +
                                   "코드 제안 시 다음 규칙을 따르세요:\n" +
                                   "1. 실행 가능한 코드만 제시\n" +
                                   "2. 설명이 필요한 경우 해당 언어의 주석 형식으로 표시\n" +
                                   "3. 마크다운 표시는 제외\n" +
                                   "4. 코드와 관련된 설명은 모두 주석으로 처리\n" +
                                   "5. 현재 작성 중인 라인의 다음 부분만 제안",
                    },
                    {
                        "role": "user",
                        "content": f"전체 코드 컨텍스트:\n{data['code']}\n\n현재 라인:\n{data['line']}\n\n현재 커서 위치:\n{data['position']}\n\n다음에 올 코드를 제안해주세요."
                    }
                ],
                max_tokens=150,
                temperature=0.3,
                presence_penalty=0.1,
                frequency_penalty=0.1,
            )

            suggestion = completion['choices'][0]['message']['content'].strip()

            # 마크다운 코드 블록 및 언어 지정자 제거
            suggestion = suggestion.replace('```', '').strip()

            print("제안할 코드:", suggestion)

            # 클라이언트에 코드 제안 전송
            await websocket.send_text(suggestion)

    except WebSocketDisconnect:
        print("클라이언트가 연결을 종료했습니다.")
