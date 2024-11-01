from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from github import Github, GithubException
from typing import Optional
import httpx
import os
from dependencies.config import get_config
from domains.users.dto import CodeExchange

config = get_config()

router = APIRouter(prefix='/users')

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