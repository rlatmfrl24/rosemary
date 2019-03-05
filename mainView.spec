# -*- mode: python -*-

block_cipher = None


a = Analysis(['View\\mainView.py'],
             pathex=['C:\\Users\\2018159\\OneDrive - CyberLogitec\\git\\herb_project\\rosemary'],
             binaries=[],
             datas=[("chromedriver.exe",".")],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='Rosemary',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )