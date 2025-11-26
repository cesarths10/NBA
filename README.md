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

This script scrapes the latest list of NBA players from RealGM and saves them to an Excel file. This file is required for the stats collection step.

**Command:**

```bash
python players.py
```

**Output:** `players.xlsx`

---

### 2. Game Logs & Stats Collection

**Script:** `stats.py`

This script reads the `players.xlsx` file generated in the previous step, scrapes the game logs for each player, and stores the processed data into a local SQLite database.

**Command:**

```bash
python stats.py
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
