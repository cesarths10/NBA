@echo off
cd /d "C:\ZyProjects\Git\NBA"
REM Check for modified files and only commit if gamelogs.db is modified
setlocal enabledelayedexpansion
set MODIFIED=0
for /f "usebackq tokens=*" %%A in (`git ls-files --modified`) do (
  if /I "%%~A"=="gamelogs.db" (
    set MODIFIED=1
  )
)
if "%MODIFIED%"=="1" (
  git add gamelogs.db
  git commit -m "Update gamelogs.db (scheduled update)" --quiet
  git push
) else (
  echo No changes to gamelogs.db; nothing to commit.
)
endlocal
