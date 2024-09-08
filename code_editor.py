import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QTextEdit
from PyQt5.Qsci import QsciScintilla, QsciLexerPython
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

class CodeEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.loadModel()

    def initUI(self):
        self.setWindowTitle('Starcoder2 Code Editor')
        self.setGeometry(100, 100, 1000, 600)

        main_widget = QWidget()
        main_layout = QHBoxLayout()

        self.editor = QsciScintilla()
        self.editor.setLexer(QsciLexerPython())
        self.editor.setUtf8(True)
        self.editor.setFont('Consolas')
        self.editor.setMarginsFont('Consolas')
        self.editor.setMarginWidth(0, '0000')
        self.editor.setMarginLineNumbers(0, True)
        self.editor.setTabWidth(4)

        self.output = QTextEdit()
        self.output.setReadOnly(True)

        button_layout = QVBoxLayout()
        self.generate_button = QPushButton('Generate')
        self.generate_button.clicked.connect(self.generateCode)
        button_layout.addWidget(self.generate_button)

        editor_layout = QVBoxLayout()
        editor_layout.addWidget(self.editor)
        editor_layout.addWidget(self.output)

        main_layout.addLayout(editor_layout)
        main_layout.addLayout(button_layout)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def loadModel(self):
        self.tokenizer = AutoTokenizer.from_pretrained("bigcode/starcoder2-3b")
        self.model = AutoModelForCausalLM.from_pretrained("bigcode/starcoder2-3b", 
                                                          device_map="auto", 
                                                          load_in_8bit=True)

    def generateCode(self):
        prompt = self.editor.text()
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        with torch.no_grad():
            outputs = self.model.generate(**inputs, max_length=len(prompt) + 100)
        generated_code = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        self.output.setPlainText(generated_code[len(prompt):])

if __name__ == '__main__':
    app = QApplication(sys.argv)
    editor = CodeEditor()
    editor.show()
    sys.exit(app.exec_())