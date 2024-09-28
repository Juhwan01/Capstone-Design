from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from github import Github
from github.GithubException import GithubException
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React 앱의 URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI")

class CodeExchange(BaseModel):
    code: str

class FileUpdate(BaseModel):
    token: str
    repo_name: str
    file_path: str
    content: str
    branch: str

class FileCreate(BaseModel):
    token: str
    repo_name: str
    file_name: str
    content: str
    branch: str

def get_github_client(token: str):
    return Github(token)

@app.post("/api/github-login")
async def github_login(code_exchange: CodeExchange):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://github.com/login/oauth/access_token",
            params={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code_exchange.code,
                "redirect_uri": GITHUB_REDIRECT_URI,
            },
            headers={"Accept": "application/json"},
        )
    
    if response.status_code == 200:
        data = response.json()
        if "error" in data:
            raise HTTPException(status_code=400, detail=data["error_description"])
        return data
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to retrieve token")


@app.get("/api/user-repos")
async def get_user_repos(token: str):
    g = get_github_client(token)
    try:
        return [repo.name for repo in g.get_user().get_repos()]
    except GithubException as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/repo-contents")
async def get_repo_contents(token: str, repo_name: str, path: str = ""):
    g = get_github_client(token)
    try:
        repo = g.get_user().get_repo(repo_name)
        contents = repo.get_contents(path)
        return [{"name": content.name, "path": content.path, "type": content.type} for content in contents]
    except GithubException as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/file-content")
async def get_file_content(token: str, repo_name: str, file_path: str):
    g = get_github_client(token)
    try:
        repo = g.get_user().get_repo(repo_name)
        file_content = repo.get_contents(file_path)
        return {"content": file_content.decoded_content.decode()}
    except GithubException as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/update-file")
async def update_file(file_update: FileUpdate):
    g = get_github_client(file_update.token)
    try:
        repo = g.get_user().get_repo(file_update.repo_name)
        contents = repo.get_contents(file_update.file_path, ref=file_update.branch)
        repo.update_file(contents.path, "Update file", file_update.content, contents.sha, branch=file_update.branch)
        return {"message": "File updated successfully"}
    except GithubException as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/create-file")
async def create_file(file_create: FileCreate):
    g = get_github_client(file_create.token)
    try:
        repo = g.get_user().get_repo(file_create.repo_name)
        repo.create_file(file_create.file_name, "Create new file", file_create.content, branch=file_create.branch)
        return {"message": "File created successfully"}
    except GithubException as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)