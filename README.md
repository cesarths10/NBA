# NBA Stats Project - Execution Guide

This document outlines the procedural order for running the Python scripts in this project to ensure data is correctly collected, processed, and visualized.

## Prerequisites

Before running the scripts, ensure you have the necessary dependencies installed:

```bash
pip install -r requirements.txt
```

## Execution Order

### 1. Player Data Collection

**Script:** `players.py`

This script scrapes the latest list of NBA players from RealGM and saves them to a CSV file. This file is required for the stats collection step.

**Command:**

```bash
python players.py
```

**Output:** `players.csv`

---

### 2. Game Logs & Stats Collection

**Script:** `stats.py`

This script updates and synchronizes player game logs into the local SQLite database (`gamelogs.db`).

- **Default Execution (Daily Incremental Refresh):**
  Automatically checks the latest date in `gamelogs.db` and queries RealGM's daily scoreboard and completed boxscores for yesterday (and any recent missing days). Makes only ~6–12 HTTP requests in seconds, preventing bot IP lockouts.
  ```bash
  python stats.py
  ```

- **Sync Specific Date or Past Days:**
  ```bash
  python stats.py --date 2026-10-24
  python stats.py --days 3
  ```

- **Current Season Sync for All Players:**
  Syncs only the active season's player game logs (`/NBA/2027`), bypassing past career history:
  ```bash
  python stats.py --season 2026-27
  ```

- **Full Career Historical Backfill (2015–Present):**
  Only needed when recreating the entire database from scratch:
  ```bash
  python stats.py --all-history
  ```

**Output:** `gamelogs.db`

---

### 3. Visualization Application

**Script:** `app.py`

This is the main application interface. It reads the data from `gamelogs.db` and launches a Streamlit web server to visualize the player stats and game logs.

**Command:**

```bash
streamlit run app.py
```

**Output:** Opens a web interface in your browser (usually at `http://localhost:8501`).

---

### Optional: Schedule Generation

**Script:** `generate_schedule.py`

This script is a standalone utility to scrape and extract NBA schedules for a specific year. It is not strictly required for the main `app.py` workflow but provides schedule data if needed.

**Command:**

```bash
python generate_schedule.py
```

**Output:** `2026-Schedules-Extracted.xlsx` (or similar depending on the year)
