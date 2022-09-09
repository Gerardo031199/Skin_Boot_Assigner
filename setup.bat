@echo on
set PY_FILE=main.py
set PROJECT_NAME=Skin Boot Assigner
set VERSION=1.0.0
set FILE_VERSION=file_version_info.txt 
set EXTRA_ARG=--add-data=resource.png;. --add-data=pes_indie.ico;. --additional-hooks-dir=. 
set ICO_DIR=pes_indie.ico

pyinstaller --onefile --noconsole "%PY_FILE%" --icon="%ICO_DIR%" --name "%PROJECT_NAME%_%VERSION%" %EXTRA_ARG% --version-file "%FILE_VERSION%"

cd dist
tar -acvf "%PROJECT_NAME%_%VERSION%.zip" * config
pause