from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.users.user_controller import router as user_router
from routers.socket.socket_controller import router as socket_router

routers = []
routers.append(user_router, socket_router)

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React 앱의 URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# user_controller 라우터 등록
app.include_router(routers)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
