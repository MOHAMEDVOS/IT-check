@echo off
echo.
echo ========================================
echo   VOS Dashboard Deploy to PythonAnywhere
echo ========================================
echo.

echo [1/3] Opening bash console...
curl -s -X POST ^
  "https://www.pythonanywhere.com/api/v0/user/mohamed404/consoles/" ^
  -H "Authorization: Token 7e56f3e0dc4e4ccef07fefca25d85138a73e2771" ^
  -H "Content-Type: application/json" ^
  -d "{\"executable\":\"bash\",\"arguments\":\"\"}" ^
  > %TEMP%\pa_console.json

type %TEMP%\pa_console.json

for /f "tokens=1 delims=," %%a in (%TEMP%\pa_console.json) do set FIRST=%%a
for /f "tokens=2 delims=:" %%a in ("%FIRST%") do set CONSOLE_ID=%%a

echo.
echo Console ID: %CONSOLE_ID%
echo Waiting for console to be ready...
timeout /t 5 /nobreak >nul

echo.
echo [2/3] Running git pull...
curl -s -X POST ^
  "https://www.pythonanywhere.com/api/v0/user/mohamed404/consoles/%CONSOLE_ID%/send_input/" ^
  -H "Authorization: Token 7e56f3e0dc4e4ccef07fefca25d85138a73e2771" ^
  -H "Content-Type: application/json" ^
  -d "{\"input\":\"cd /home/mohamed404/IT-check && git pull origin main\n\"}"

echo Waiting for git pull to finish...
timeout /t 10 /nobreak >nul

echo.
echo [3/3] Reloading web app...
curl -s -X POST ^
  "https://www.pythonanywhere.com/api/v0/user/mohamed404/webapps/mohamed404.pythonanywhere.com/reload/" ^
  -H "Authorization: Token 7e56f3e0dc4e4ccef07fefca25d85138a73e2771"

echo.
echo ========================================
echo   Done! Check: https://mohamed404.pythonanywhere.com
echo ========================================
echo.
pause
