import React, { useEffect, useRef, forwardRef, useImperativeHandle } from 'react';
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import 'xterm/css/xterm.css';

const TerminalComponent = forwardRef((props, ref) => {
  const terminalRef = useRef(null);
  const ws = useRef(null);
  const term = useRef(null);

  useImperativeHandle(ref, () => ({
    executeCommand: (command) => {
      if (ws.current && ws.current.readyState === WebSocket.OPEN) {
        ws.current.send(command);
        term.current.writeln(`Executing: ${command}`);
      } else {
        term.current.writeln('WebSocket is not connected. Please try again.');
      }
    },
    stopExecution: () => {
      if (ws.current && ws.current.readyState === WebSocket.OPEN) {
        ws.current.send('STOP_EXECUTION');
        term.current.writeln('Sending stop command...');
      } else {
        term.current.writeln('WebSocket is not connected. Cannot stop execution.');
      }
    }
  }));

  useEffect(() => {
    term.current = new Terminal({
      cursorBlink: true,
      cols: 80,
      rows: 24,
      scrollback: 1000,
      fontFamily: 'Consolas, "Courier New", monospace',
      fontSize: 14,
    });
    const fitAddon = new FitAddon();
    term.current.loadAddon(fitAddon);

    term.current.open(terminalRef.current);
    fitAddon.fit();

    ws.current = new WebSocket('ws://localhost:8000/ws');

    ws.current.onopen = () => {
      term.current.writeln('Connected to the server');
    };

    ws.current.onmessage = (event) => {
      const lines = event.data.split('\n');
      lines.forEach((line) => {
        term.current.writeln(line);
      });
    };

    ws.current.onerror = (error) => {
      term.current.writeln(`WebSocket Error: ${error.message}`);
    };

    ws.current.onclose = () => {
      term.current.writeln('Disconnected from the server');
    };

    const handleKeyDown = (event) => {
      if (event.ctrlKey && event.key === 'c') {
        event.preventDefault(); // 브라우저의 기본 동작 방지
        term.current.writeln('^C');
        ref.current.stopExecution();
      }
    };

    // xterm.js의 onKey 이벤트를 사용하여 Ctrl+C 처리
    term.current.onKey(({ key, domEvent }) => {
      if (domEvent.ctrlKey && domEvent.key === 'c') {
        term.current.writeln('^C');
        ref.current.stopExecution();
      }
    });

    // 터미널에 포커스가 있을 때만 키 이벤트를 처리
    terminalRef.current.addEventListener('focus', () => {
      window.addEventListener('keydown', handleKeyDown);
    });

    terminalRef.current.addEventListener('blur', () => {
      window.removeEventListener('keydown', handleKeyDown);
    });

    return () => {
      term.current.dispose();
      if (ws.current) {
        ws.current.close();
      }
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [ref]);

  return (
    <div>
      <div ref={terminalRef} style={{ width: '100%', height: '40vh' }} tabIndex="0" />
    </div>
  );
});

export default TerminalComponent;