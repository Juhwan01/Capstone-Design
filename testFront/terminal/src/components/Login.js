import React from 'react';

function Login() {
  const handleLogin = () => {
    const scope = 'repo'; // GitHub 저장소에 대한 전체 접근 권한 요청
    window.location.href = `https://github.com/login/oauth/authorize?client_id=${process.env.REACT_APP_GITHUB_CLIENT_ID}&redirect_uri=http://localhost:3000/callback&scope=${scope}`;
  };

  return (
    <div>
      <h1>GitHub Repository Manager</h1>
      <button onClick={handleLogin}>GitHub로 로그인</button>
    </div>
  );
}

export default Login;