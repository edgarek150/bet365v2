@echo off
cd /d "%~dp0"

:: Kill any previous Chrome/scraper instances on port 9222
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":9222"') do taskkill /PID %%a /F 2>nul
timeout /t 2 /nobreak >nul

:: Start Chrome with remote debugging (minimized)
start /min "" "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --no-first-run ^
  --no-default-browser-check ^
  --disable-default-apps ^
  --user-data-dir="%TEMP%\chrome-scraper"

timeout /t 3 /nobreak >nul

:: Start the scraper
python main.py
