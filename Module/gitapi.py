import streamlit as st
import requests
from github import Github
from github.GithubException import GithubException

def github_auth(access_token):
    return Github(access_token)

def get_user_repos(g):
    return [repo.name for repo in g.get_user().get_repos()]

def get_repo_contents(g, repo_name, path=''):
    repo = g.get_user().get_repo(repo_name)
    contents = repo.get_contents(path)
    return contents

def get_file_content(g, repo_name, file_path):
    repo = g.get_user().get_repo(repo_name)
    file_content = repo.get_contents(file_path)
    return file_content.decoded_content.decode()

def get_default_branch(repo):
    return repo.default_branch

def stage_changes(repo, file_path, new_content, branch):
    try:
        contents = repo.get_contents(file_path, ref=branch)
        repo.update_file(contents.path, "Staging changes", new_content, contents.sha, branch=branch)
        return True
    except GithubException as e:
        if e.status == 404:
            # 파일이 존재하지 않는 경우, 새로 생성
            repo.create_file(file_path, "Creating new file", new_content, branch=branch)
            return True
        else:
            raise e

def commit_and_push_changes(repo, commit_message, branch):
    # PyGithub에서는 커밋과 푸시가 자동으로 이루어집니다.
    # 이 함수는 실제 커밋과 푸시 동작을 시뮬레이션합니다.
    latest_commit = repo.get_commits(sha=branch)[0]
    return latest_commit.sha

# Streamlit UI
st.title('GitHub Repository Manager')

access_token = st.text_input('GitHub 액세스 토큰을 입력하세요:', type='password')

if access_token:
    try:
        g = github_auth(access_token)
        st.success('GitHub에 성공적으로 연결되었습니다!')

        repos = get_user_repos(g)
        selected_repo = st.selectbox('레포지토리를 선택하세요:', repos)

        if selected_repo:
            repo = g.get_user().get_repo(selected_repo)
            default_branch = get_default_branch(repo)
            st.write(f'선택된 레포지토리: {selected_repo} (기본 브랜치: {default_branch})')

            action = st.radio("수행할 작업을 선택하세요:", ('기존 파일 수정', '새 파일 추가'))

            if action == '기존 파일 수정':
                try:
                    contents = get_repo_contents(g, selected_repo)
                    files = [content.path for content in contents if content.type == 'file']
                    selected_file = st.selectbox('수정할 파일을 선택하세요:', files)

                    if selected_file:
                        file_content = get_file_content(g, selected_repo, selected_file)
                        new_content = st.text_area('파일 내용:', value=file_content, height=300)

                        if st.button('변경 사항 스테이징 및 커밋'):
                            try:
                                stage_changes(repo, selected_file, new_content, default_branch)
                                commit_sha = commit_and_push_changes(repo, "Update file", default_branch)
                                st.success(f'변경 사항이 성공적으로 커밋되었습니다. 커밋 SHA: {commit_sha}')
                            except Exception as e:
                                st.error(f'변경 사항 처리 중 오류가 발생했습니다: {str(e)}')

                except Exception as e:
                    st.error(f'파일 목록을 불러오는 중 오류가 발생했습니다: {str(e)}')

            elif action == '새 파일 추가':
                new_file_name = st.text_input('새 파일 이름을 입력하세요:')
                new_file_content = st.text_area('파일 내용을 입력하세요:', height=300)
                
                if st.button('파일 생성 및 커밋'):
                    try:
                        stage_changes(repo, new_file_name, new_file_content, default_branch)
                        commit_sha = commit_and_push_changes(repo, "Create new file", default_branch)
                        st.success(f'새 파일이 성공적으로 생성되고 커밋되었습니다. 커밋 SHA: {commit_sha}')
                    except Exception as e:
                        st.error(f'파일 생성 중 오류가 발생했습니다: {str(e)}')

    except Exception as e:
        st.error(f'GitHub 연결 중 오류가 발생했습니다: {str(e)}')