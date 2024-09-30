# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# PyTorch 관련 파일 수집
torch_datas, torch_binaries, torch_hiddenimports = collect_all('torch')

# Transformers 관련 파일 수집
transformers_datas, transformers_binaries, transformers_hiddenimports = collect_all('transformers')

a = Analysis(['code_editor.py'],
             pathex=[],
             binaries=[],
             datas=[],
             hiddenimports=['torch', 'transformers'] + torch_hiddenimports + transformers_hiddenimports,
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

# PyTorch 관련 파일 추가
a.datas += torch_datas
a.binaries += torch_binaries

# Transformers 관련 파일 추가
a.datas += transformers_datas
a.binaries += transformers_binaries

# Starcoder2 모델 파일 추가
import tempfile
from transformers import AutoTokenizer, AutoModelForCausalLM

model_name = "bigcode/starcoder2-3b"
with tempfile.TemporaryDirectory() as tmpdirname:
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    tokenizer.save_pretrained(tmpdirname)
    model.save_pretrained(tmpdirname)
    
    for root, dirs, files in os.walk(tmpdirname):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, tmpdirname)
            a.datas += [(f'transformers/{rel_path}', full_path, 'DATA')]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,  
          [],
          name='StarcodeEditor',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )