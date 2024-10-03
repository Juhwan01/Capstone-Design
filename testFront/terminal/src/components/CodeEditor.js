import React from 'react';
import Editor from "@monaco-editor/react";

function CodeEditor({ code, setCode }) {
  return (
    <Editor
      height="40vh"
      defaultLanguage="python"
      value={code}
      onChange={setCode}
      theme="vs-dark"
    />
  );
}

export default CodeEditor;