@echo off
cd /d "%~dp0"
REM Check for modified files and commit if gamelogs.db or players.csv is modified
setlocal enabledelayedexpansion
set MODIFIED=0
for /f "usebackq tokens=*" %%A in (`git status --porcelain gamelogs.db players.csv 2^>nul`) do (
  set MODIFIED=1
)
if "%MODIFIED%"=="1" (
  git add gamelogs.db players.csv
  git commit -m "Update gamelogs.db and players.csv (scheduled update)" --quiet
  git push
) else (
  echo No changes to gamelogs.db or players.csv; nothing to commit.
)
endlocal
