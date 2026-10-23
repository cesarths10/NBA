@echo off
cd /d "%~dp0"
echo ========================================================
echo [1/3] Refreshing NBA players roster (players.py)...
echo ========================================================
python players.py

echo ========================================================
echo [2/3] Scraping latest game logs and stats (stats.py)...
echo ========================================================
python stats.py

echo ========================================================
echo [3/3] Checking for changes and pushing to GitHub...
echo ========================================================
call commit_db.bat

echo ========================================================
echo Daily NBA refresh and cloud sync completed successfully!
echo ========================================================
