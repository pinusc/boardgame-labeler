call .\wenv\Scripts\activate.bat
pip.exe install -r requirements.txt
pyinstaller.exe main.spec
