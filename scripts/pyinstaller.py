import PyInstaller.__main__
import sys
import tomli
import os
from pathlib import Path

ROOT_DIR = Path('scripts/pyinstaller.py').parent.parent.resolve()
with open(ROOT_DIR / 'pyproject.toml', 'rb') as f:
    conf = tomli.load(f)

PLATFORM = sys.platform
VERSION = conf['tool']['poetry']['version']
NAME = conf['tool']['poetry']['name']
OUT_NAME = f'boardgame-labeler-{VERSION}-{PLATFORM}'

pyinstaller_dir = ROOT_DIR / 'pyinstaller'
workpath = pyinstaller_dir / f'build-{PLATFORM}'
distpath = pyinstaller_dir / 'dist'
res_dir = ROOT_DIR / 'res'
add_data = str(res_dir / '*') + os.pathsep + 'res'

PyInstaller.__main__.run([
    'main.py',
    '--onefile',
    '--windowed',
    '--specpath=pyinstaller',
    f'--workpath={workpath}',
    f'--distpath={distpath}',
    f'--add-data={add_data}',
    '--hidden-import=pkg_resources',
    f'--name={OUT_NAME}' 
])
