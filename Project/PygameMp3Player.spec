# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['PygameMp3Player.py'],
             pathex=['D:\\Python\\Projects\\PMP\\PygameMp3Player\\venv\\Lib\\site-packages'],
             binaries=[],
             datas=[],
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
          [
              ('theme\\default.json', 'theme\\default.json', 'DATA'),
              ('img\\btn\\order\\0.png', 'img\\btn\\order\\0.png', 'DATA'),
              ('img\\btn\\order\\1.png', 'img\\btn\\order\\1.png', 'DATA'),
              ('img\\btn\\order\\2.png', 'img\\btn\\order\\2.png', 'DATA'),
              ('img\\btn\\play\\next.bmp', 'img\\btn\\play\\next.bmp', 'DATA'),
              ('img\\btn\\play\\pause.bmp', 'img\\btn\\play\\pause.bmp', 'DATA'),
              ('img\\btn\\play\\play.bmp', 'img\\btn\\play\\play.bmp', 'DATA'),
              ('img\\btn\\play\\previous.bmp', 'img\\btn\\play\\previous.bmp', 'DATA'),
              ('img\\btn\\play\\up.bmp', 'img\\btn\\play\\up.bmp', 'DATA'), ('img\\None.png', 'img\\None.png', 'DATA'),
              ('font\\msyhl.ttc', 'font\\msyhl.ttc', 'DATA'),
              ('Pinyin2Hanzi\\data\\dag_char.json', 'Pinyin2Hanzi\\data\\dag_char.json', 'DATA'),
              ('Pinyin2Hanzi\\data\\dag_phrase.json', 'Pinyin2Hanzi\\data\\dag_phrase.json', 'DATA'),
              ('Pinyin2Hanzi\\data\\hmm_emission.json', 'Pinyin2Hanzi\\data\\hmm_emission.json', 'DATA'),
              ('Pinyin2Hanzi\\data\\hmm_py2hz.json', 'Pinyin2Hanzi\\data\\hmm_py2hz.json', 'DATA'),
              ('Pinyin2Hanzi\\data\\hmm_start.json', 'Pinyin2Hanzi\\data\\hmm_start.json', 'DATA'),
              ('Pinyin2Hanzi\\data\\hmm_transition.json', 'Pinyin2Hanzi\\data\\hmm_transition.json', 'DATA')
          ],
          name='PygameMp3Player',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True)
