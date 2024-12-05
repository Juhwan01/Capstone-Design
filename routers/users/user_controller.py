from fastapi import APIRouter, HTTPException, Header
from github import Github, GithubException
from typing import Optional
import httpx
import os, git
from dependencies.config import get_config
from domains.users.dto import CodeExchange, FileCreate, FileUpdate, CloneRequest

config = get_config()

router = APIRouter(prefix='/users',tags=["Users"])

def get_github_client(token: str):
    return Github(token)

def get_token_from_header(authorization: str) -> str:
    if authorization.startswith("Bearer "):
        return authorization.replace("Bearer ", "")
    return authorization

# GitHub 로그인 엔드포인트
@router.post("/api/github-login")
async def github_login(code_exchange: CodeExchange):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://github.com/login/oauth/access_token",
            params={
                "client_id": config.GITHUB_CLIENT_ID,
                "client_secret": config.GITHUB_CLIENT_SECRET,
                "code": code_exchange.code,
                "redirect_uri": config.GITHUB_REDIRECT_URI,
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
# 사용자 저장소 가져오기 엔드포인트
@router.get("/api/user-repos")
async def get_user_repos(authorization: str = Header(..., description="Bearer 토큰")):
    token = get_token_from_header(authorization)
    g = get_github_client(token)
    try:
        return [repo.name for repo in g.get_user().get_repos()]
    except GithubException as e:
        raise HTTPException(status_code=400, detail=str(e))

# 특정 저장소 내용 가져오기 엔드포인트
@router.get("/api/repo-contents")
async def get_repo_contents(
    repo_name: str,
    path: Optional[str] = "",
    authorization: str = Header(..., description="Bearer 토큰")
):
    token = get_token_from_header(authorization)
    g = get_github_client(token)
    try:
        repo = g.get_user().get_repo(repo_name)
        contents = repo.get_contents(path)
        if not isinstance(contents, list):
            contents = [contents]
        return [{"name": content.name, "path": content.path, "type": content.type} for content in contents]
    except GithubException as e:
        raise HTTPException(status_code=400, detail=str(e))

# 파일 내용 가져오기 엔드포인트
@router.get("/api/file-content")
async def get_file_content(
    repo_name: str,
    file_path: str,
    authorization: str = Header(..., description="Bearer 토큰")
):
    token = get_token_from_header(authorization)
    g = get_github_client(token)
    try:
        repo = g.get_user().get_repo(repo_name)
        file_content = repo.get_contents(file_path)
        return {"content": file_content.decoded_content.decode()}
    except GithubException as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/api/update-file")
async def update_file(file_update: FileUpdate):
    g = get_github_client(file_update.token)
    try:
        repo = g.get_user().get_repo(file_update.repo_name)
        contents = repo.get_contents(file_update.file_path, ref=file_update.branch)
        repo.update_file(contents.path, file_update.commit_message, file_update.content, contents.sha, branch=file_update.branch)
        return {"message": "File updated successfully"}
    except GithubException as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/api/create-file")
async def create_file(file_create: FileCreate):
    g = get_github_client(file_create.token)
    try:
        repo = g.get_user().get_repo(file_create.repo_name)
        repo.create_file(file_create.file_name, file_create.commit_message, file_create.content, branch=file_create.branch)
        return {"message": "File created successfully"}
    except GithubException as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/clone-repo")
def clone_repository(request: CloneRequest):
    repo_url = request.repo_url
    destination = request.destination
    
    if not repo_url.startswith("https://github.com/"):
        raise HTTPException(status_code=400, detail="Invalid GitHub repository URL")
    
    # Check if destination directory exists
    if os.path.exists(destination):
        raise HTTPException(status_code=400, detail="Destination directory already exists")
    
    try:
        git.Repo.clone_from(repo_url, destination)
        return {"message": "Repository cloned successfully", "path": destination}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
