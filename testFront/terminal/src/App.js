import React, { useState, useRef, useCallback } from 'react';
import TerminalComponent from './components/Terminal';
import CodeEditor from './components/CodeEditor';

function App() {
  const [code, setCode] = useState('# Write your Python code here\n');
  const terminalRef = useRef(null);

  const runCode = useCallback(() => {
    if (terminalRef.current) {
      terminalRef.current.executeCommand(`EXECUTE_PYTHON:${code}`);
    } else {
      console.error('Terminal reference is not available');
    }
  }, [code]);

  return (
    <div className="App">
      <h1>Web IDE</h1>
      <CodeEditor code={code} setCode={setCode} />
      <button onClick={runCode}>Run Code</button>
      <TerminalComponent ref={terminalRef} />
    </div>
  );
}

export default App;