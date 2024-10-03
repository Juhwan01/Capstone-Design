import asyncio
import os
import tempfile
import signal
import psutil
import platform  # 플랫폼 확인을 위해 import 추가
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def clean_ansi(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

current_process = None
process_task = None

def terminate_process_tree(pid):
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            child.terminate()
        parent.terminate()
        gone, still_alive = psutil.wait_procs(children + [parent], timeout=3)
        for p in still_alive:
            p.kill()
    except psutil.NoSuchProcess:
        pass

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global current_process, process_task
    await websocket.accept()
    await websocket.send_text("WebSocket connection established")

    try:
        while True:
            data = await websocket.receive_text()
            if data.startswith("EXECUTE_PYTHON:"):
                if current_process:
                    terminate_process_tree(current_process.pid)
                    await websocket.send_text("Previous process terminated.")
                    if process_task:
                        process_task.cancel()
                        try:
                            await process_task
                        except asyncio.CancelledError:
                            pass

                code = data[15:]
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
                    tmp.write(code)
                    tmp_filename = tmp.name

                # 플랫폼에 따라 다른 방식으로 서브프로세스 실행
                if platform.system() == "Windows":
                    current_process = await asyncio.create_subprocess_shell(
                        f"python {tmp_filename}",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                else:  # Unix 계열
                    current_process = await asyncio.create_subprocess_shell(
                        f"python {tmp_filename}",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        preexec_fn=os.setsid  # Unix에서만 새로운 프로세스 그룹 생성
                    )

                async def run_process():
                    try:
                        while True:
                            line = await current_process.stdout.readline()
                            if line:
                                await websocket.send_text(clean_ansi(line.decode()))
                            else:
                                break
                        
                        await current_process.wait()
                        if current_process.returncode != 0:
                            stderr = await current_process.stderr.read()
                            await websocket.send_text(clean_ansi(stderr.decode()))
                    finally:
                        os.unlink(tmp_filename)
                        await websocket.send_text("Process completed.")

                process_task = asyncio.create_task(run_process())

            elif data == "STOP_EXECUTION":
                if current_process:
                    terminate_process_tree(current_process.pid)
                    await websocket.send_text("Execution forcefully stopped.")
                    if process_task:
                        process_task.cancel()
                        try:
                            await process_task
                        except asyncio.CancelledError:
                            pass
                    current_process = None
                    process_task = None
                else:
                    await websocket.send_text("No process running.")

            else:
                await websocket.send_text(f"Received: {data}")
    except Exception as e:
        await websocket.send_text(f"Error: {str(e)}")
    finally:
        if current_process:
            terminate_process_tree(current_process.pid)
        if process_task:
            process_task.cancel()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
