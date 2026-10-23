# Import core utilities for filesystem, regex, CLI args, timing, datetime, and concurrency
import os
import re
import sys
import time
from datetime import datetime
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
# Import data processing, networking, database, and parsing libraries
import pandas as pd
import requests
import sqlite3
from bs4 import BeautifulSoup
from bisect import bisect_right
# Import browser automation components for fallback scraping
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Clean and normalize raw table header strings by removing special characters and spaces
def clean_header(col):
    # Return empty string if column is None
    if col is None:
        return ''
    s = str(col).strip()
    # Return empty string if stripped header is blank
    if not s:
        return ''
    # Replace spaces with underscores
    s = re.sub(r"\s+", '_', s)
    # Strip any characters that are not alphanumeric, underscore, or percent
    s = re.sub(r'[^A-Za-z0-9_%]', '', s)
    return s

# Base site URL for resolving relative player links
BASE = 'https://basketball.realgm.com'

# Construct the full RealGM game logs URL for a given player summary profile URL
def build_gamelogs_url(summary_url: str) -> str:
    # Return empty string if summary URL is empty
    if not summary_url:
        return ''
    # Prepend base domain if summary URL is a relative path
    if summary_url.startswith('/'):
        summary_url = urljoin(BASE, summary_url)

    # Extract numeric RealGM player ID from the /Summary/<id> URL segment
    m = re.search(r"/Summary/(\d+)", summary_url)
    # If standard summary pattern is not found, attempt trailing digits extraction
    if not m:
        parts = summary_url.rstrip('/').split('/')
        # Verify if final URL segment contains digits
        if parts and parts[-1].isdigit():
            pid = parts[-1]
        # Return empty string if no valid player ID can be extracted
        else:
            return ''
    # Assign matched player ID group
    else:
        pid = m.group(1)

    # Replace /Summary/<id> segment with /GameLogs/<id>/NBA/All
    gamelogs = re.sub(r"/Summary/\d+", f"/GameLogs/{pid}/NBA/All", summary_url)
    # Fallback path construction if regex substitution did not apply
    if '/GameLogs/' not in gamelogs:
        base_player = re.sub(r"/Summary/\d+", "", summary_url)
        gamelogs = base_player.rstrip('/') + f"/GameLogs/{pid}/NBA/All"

    return gamelogs

# Fetch webpage HTML using standard requests with automated retries and timeout
def fetch_html(url: str, headers=None, timeout=15) -> str:
    # Set default modern desktop browser User-Agent header
    headers = headers or {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    tries = 3
    # Retry up to 3 times on transient network failures
    for attempt in range(1, tries + 1):
        # Safely execute GET request with custom headers
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            # Return text if request was successful
            if resp.status_code == 200:
                return resp.text
        # Ignore network errors on intermediate retries
        except Exception:
            pass
        # Brief backoff pause between retry attempts
        time.sleep(1)
    # Return empty string if all retries failed
    return ''

# Batch fetch URLs using curl_cffi with Chrome 120 TLS fingerprinting to bypass anti-bot protections
def fetch_htmls_curl_cffi(urls: list[str], timeout: int = 20) -> list[str]:
    # Safely initialize curl_cffi session with Chrome impersonation
    try:
        from curl_cffi import requests
        session = requests.Session(impersonate="chrome120")
        results = []
        # Fetch each URL in the batch sequentially using the impersonated session
        for url in urls:
            # Safely request page content
            try:
                resp = session.get(url, timeout=timeout)
                # Append page text if status is 200 OK
                if resp.status_code == 200:
                    results.append(resp.text)
                # Append blank string on non-200 responses
                else:
                    results.append('')
            # Append blank string if individual request raised an exception
            except Exception:
                results.append('')
        return results
    # Catch module import error or session startup failure
    except Exception:
        return []

# Fallback headless Chrome scraper using Selenium for JavaScript-rendered game log tables
def fetch_htmls_selenium(urls: list[str], timeout: int = 30) -> list[str]:
    # Configure headless Chrome browser options
    chrome_options = Options()
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    driver = None
    results = []
    # Initialize driver and iterate through URLs
    try:
        # Install and launch matching ChromeDriver binary
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
        driver.set_page_load_timeout(timeout)
        driver.implicitly_wait(2)

        # Scrape each URL in the target list
        for url in urls:
            # Safely fetch page and wait for table elements to render
            try:
                driver.get(url)
                # Wait up to 5 seconds for table body rows to appear in the DOM
                try:
                    wait = WebDriverWait(driver, 5)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
                # Proceed even if explicit wait times out
                except TimeoutException:
                    pass
                results.append(driver.page_source)
            # Append empty string if page load failed
            except Exception:
                results.append('')
            # Brief pause between browser requests
            time.sleep(0.5)
    # Populate blank results if driver failed completely
    except WebDriverException:
        results = [''] * len(urls)
    # Guarantee that browser process is cleanly terminated
    finally:
        try:
            if driver:
                driver.quit()
        except Exception:
            pass
    return results

# Parse game logs table HTML into a structured pandas DataFrame
def parse_gamelogs_table(html: str) -> pd.DataFrame:
    # Parse HTML using fast lxml engine
    soup = BeautifulSoup(html, 'lxml')

    # Primary selector: fixed-table-body container table
    table = soup.select_one('div.fixed-table-body table')
    # Secondary selector: data-toggle table attribute
    if not table:
        table = soup.select_one('table[data-toggle="table"]')
    
    # Fallback selector: search all tables and select the one with the most rows
    if not table:
        tables = soup.find_all('table')
        # Select table containing the maximum number of rows
        if tables:
            table = max(tables, key=lambda t: len(t.find_all('tr')))
        else:
            table = None
            
    # Return empty DataFrame if no valid table was found
    if not table:
        return pd.DataFrame()

    headers = []
    thead = table.find('thead')
    # Extract column names from the thead element
    if thead:
        for th in thead.find_all('th'):
            text = th.get_text(strip=True)
            headers.append(text)
    # Fallback to generating generic col_i headers if thead is absent
    if not headers:
        tr0 = table.find('tr')
        cols = len(tr0.find_all(['td','th'])) if tr0 else 0
        headers = [f'col_{i}' for i in range(cols)]

    rows = []
    tbody = table.find('tbody')
    # Return empty DataFrame if table has no tbody element
    if not tbody:
        return pd.DataFrame()

    # Iterate through all rows in table body to extract cell values and links
    for tr in tbody.find_all('tr'):
        cells = tr.find_all('td')
        # Skip empty rows
        if not cells:
            continue
        row = {}
        # Map each cell to its corresponding header name
        for i, td in enumerate(cells):
            key = headers[i] if i < len(headers) else f'col_{i}'
            a = td.find('a')
            # Extract both text and absolute href if cell contains an anchor tag
            if a and a.get('href'):
                row[key] = a.get_text(strip=True)
                href = a['href']
                row[f'{key}Href'] = urljoin(BASE, href) if href.startswith('/') else href
            # Extract plain cell text if no link is present
            else:
                row[key] = td.get_text(strip=True)
        rows.append(row)

    # Return empty DataFrame if no game rows were extracted
    if not rows:
        return pd.DataFrame()

    # Construct and return pandas DataFrame from extracted rows
    df = pd.DataFrame(rows)
    return df

# Scrape all 4 game types (Reg, Playoffs, Play-In, Preseason) for a specific player and clean the data
def process_player(player_name: str, summary_href: str, out_dir: str) -> pd.DataFrame:
    # Build the player's base game logs URL
    gamelogs_url = build_gamelogs_url(summary_href)
    # Return empty DataFrame if URL could not be constructed
    if not gamelogs_url:
        return pd.DataFrame()
    
    # URL suffixes and labels for all 4 game categories
    suffixes = ['Reg', 'Playoffs', 'Play-In', 'Preseason']
    game_types = ['Regular Season', 'Playoffs', 'Play-In', 'Preseason']
    urls = [f"{gamelogs_url}/{s}" for s in suffixes]
    
    # Primary scrape: Attempt batch fetch with curl_cffi Chrome impersonation
    htmls = fetch_htmls_curl_cffi(urls)
    # Fallback scrape: Use headless Selenium if curl_cffi returned no content
    if not any(htmls):
        htmls = fetch_htmls_selenium(urls)
    
    dfs = []
    # Parse table HTML for each game category
    for gt, html in zip(game_types, htmls):
        # Skip if HTML is empty
        if not html:
            continue
        df_parsed = parse_gamelogs_table(html)
        # Skip if no rows were parsed from table
        if df_parsed.empty:
            continue
        # Tag DataFrame with its game category
        df_parsed['GameType'] = gt
        dfs.append(df_parsed)
        
    # Return empty DataFrame if no game logs were retrieved across all categories
    if not dfs:
        return pd.DataFrame()
        
    # Concatenate all game types into a single player DataFrame
    df = pd.concat(dfs, ignore_index=True)
    
    date_col = None
    # Locate the Date column case-insensitively
    for c in df.columns:
        if str(c).strip().lower() == 'date':
            date_col = c
            break
    # Fallback to first column if no date column matched
    if date_col is None:
        date_col = df.columns[0]

    # Parse date strings into datetime objects using MM/DD/YYYY format
    parsed_dates = pd.to_datetime(df[date_col], errors='coerce', format='%m/%d/%Y')
    df['Date_Parsed'] = parsed_dates
    
    # Filter out historical logs prior to the 2015-16 season kickoff (2015-10-27)
    df = df[df['Date_Parsed'] >= datetime(2015, 10, 27)].copy()
    # Return empty DataFrame if no modern games remain after date filtering
    if df.empty:
        return pd.DataFrame()
        
    # Calculate NBA season format (e.g. 2026-27) based on game date
    def calc_season(d):
        if pd.isna(d):
            return None
        # Games from August onward belong to the upcoming season end year
        season_end = d.year + 1 if d.month >= 8 else d.year
        return f"{season_end-1}-{str(season_end)[-2:]}"
        
    # Populate the Season label column
    df['Season'] = df['Date_Parsed'].apply(calc_season)

    # Enforce official 2026-27 schedule (Tuesday, October 20, 2026 to Sunday, April 11, 2027)
    # Reclassify any 'Regular Season' games played before October 20, 2026 as 'Preseason'
    mask_early_2026 = (df['Season'] == '2026-27') & (df['GameType'] == 'Regular Season') & (df['Date_Parsed'] < datetime(2026, 10, 20))
    df.loc[mask_early_2026, 'GameType'] = 'Preseason'

    # Reclassify any 2026-27 Regular Season games played after April 11, 2027 as 'Playoffs'
    mask_late_2026 = (df['Season'] == '2026-27') & (df['GameType'] == 'Regular Season') & (df['Date_Parsed'] > datetime(2027, 4, 11))
    df.loc[mask_late_2026, 'GameType'] = 'Playoffs'

    df.drop(columns=['Date_Parsed'], inplace=True, errors='ignore')

    # Insert player metadata columns at the beginning of the DataFrame
    df.insert(0, 'Player', player_name)
    m = re.search(r"/Summary/(\d+)", summary_href)
    pid = m.group(1) if m else ''
    df.insert(1, 'PlayerID', pid)
    df.insert(2, 'SummaryHref', summary_href)
    df.insert(3, 'GameLogsURL', gamelogs_url)
    
    # Standardize column headers to match application schema
    rename_map = {
        'W/L': 'WL',
        'W / L': 'WL',
        'W-L': 'WL',
        'FG%': 'FGPercent',
        '3PM': 'TPM',
        '3PA': 'TPA',
        '3P%': 'TPPercent',
        'FT%': 'FTPercent',
        'Min': 'MIN',
        'MIN': 'MIN',
        'GameLogsUrl': 'GameLogsURL',
    }
    df = df.rename(columns=rename_map)

    # Cast integer stat columns to integers with 0 fallback
    int_cols = ['PTS', 'FGM', 'FGA', 'TPM', 'TPA', 'FTM', 'FTA', 'ORB', 'DRB', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF']
    for c in int_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype(int)
            
    # Cast percentage and efficiency columns to floats with 0.0 fallback
    float_cols = ['FGPercent', 'TPPercent', 'FTPercent', 'FIC']
    for c in float_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0.0).astype(float)

    return df

# Main orchestration function to scrape all players concurrently and write to SQLite
def main(players_file: str = None, workers: int = 6, limit: int = None, season_filter: str = None):
    out_dir = os.path.dirname(os.path.abspath(__file__))
    # Resolve default players file if not specified
    if not players_file:
        default_csv = os.path.join(out_dir, 'players.csv')
        default_xlsx = os.path.join(out_dir, 'players.xlsx')
        players_file = default_csv if os.path.exists(default_csv) else default_xlsx

    # Abort if players file does not exist
    if not os.path.exists(players_file):
        print(f"File not found: {players_file}")
        return

    # Load players roster file from CSV or Excel
    try:
        if players_file.endswith('.csv'):
            players_df = pd.read_csv(players_file)
        else:
            players_df = pd.read_excel(players_file)
    # Catch file read errors
    except Exception as e:
        print(f"Error reading {players_file}: {e}")
        return

    # Verify that required player identifier columns exist in roster DataFrame
    if 'PlayerHref' not in players_df.columns and 'Player' not in players_df.columns:
        print("Required columns missing from players file.")
        return

    # Convert DataFrame row into worker arguments tuple (name, href, output_dir)
    def player_row_to_args(row, idx):
        player = row.get('Player', '')
        href = row.get('PlayerHref', '')
        # Fall back to checking Player cell for embedded URL
        if not href and isinstance(row.get('Player', ''), str):
            if row.get('Player', '').startswith('http') or row.get('Player', '').startswith('/'):
                href = row.get('Player')
        # Skip if no player URL exists
        if not href:
            return None
        return (player or f'player_{idx}', href, out_dir)
    
    # Generate list of worker argument tuples for all players
    player_args = [player_row_to_args(row, idx) for idx, row in players_df.iterrows()]
    player_args = [a for a in player_args if a is not None]
    
    # Optionally limit number of players processed for testing
    if limit:
        player_args = player_args[:limit]
        print(f"Limiting scrape to first {limit} players.")

    all_frames = []
    max_workers = min(workers, len(player_args)) if player_args else 1
    total_players = len(player_args)
    completed = 0

    print(f"Starting stats collection for {total_players} players with {max_workers} concurrent workers...")

    # Execute concurrent scraping with ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all player tasks to the thread pool
        futures = {executor.submit(process_player, *args): args[0] for args in player_args}
        # Process completed tasks as they finish
        for future in as_completed(futures):
            p_name = futures[future]
            completed += 1
            # Retrieve player scrape result DataFrame
            try:
                df = future.result()
                # Process non-empty game logs
                if not df.empty:
                    # Apply optional single-season filter
                    if season_filter:
                        df = df[df['Season'] == season_filter]
                    # Append valid game logs to collection list
                    if not df.empty:
                        all_frames.append(df)
                        print(f"[{completed}/{total_players}] {p_name}: {len(df)} games collected")
                    else:
                        print(f"[{completed}/{total_players}] {p_name}: 0 games for season {season_filter}")
                else:
                    print(f"[{completed}/{total_players}] {p_name}: 0 games found")
            # Log task exception without halting the worker loop
            except Exception as e:
                print(f"[{completed}/{total_players}] {p_name}: Error {e}")

    # Exit if no games were collected across all players
    if not all_frames:
        print("No games collected to write.")
        return

    # Combine all scraped player game logs into a single DataFrame
    combined_new = pd.concat(all_frames, ignore_index=True)
    merged = combined_new

    # Drop duplicate game rows safely
    try:
        merged_deduped = merged.drop_duplicates().reset_index(drop=True)
    except Exception:
        merged_deduped = merged.copy() if hasattr(merged, 'copy') else merged

    # Clean and standardize all column headers
    merged.columns = [clean_header(c) for c in merged.columns]

    # Merge accurate player position from players roster file
    try:
        # Check if position column exists in players roster
        if 'Pos' in players_df.columns:
            # Extract numeric PlayerID from PlayerHref if missing
            if 'PlayerID' not in players_df.columns and 'PlayerHref' in players_df.columns:
                players_df['PlayerID'] = players_df['PlayerHref'].astype(str).str.extract(r'/Summary/(\d+)', expand=False).fillna('')

            # Clean PlayerID string whitespace in both tables
            if 'PlayerID' in players_df.columns:
                players_df['PlayerID'] = players_df['PlayerID'].astype(str).str.strip()

            if 'PlayerID' in merged_deduped.columns:
                merged_deduped['PlayerID'] = merged_deduped['PlayerID'].astype(str).str.strip()

            # Preserve scraped position before override
            if 'Pos_Scraped' not in merged_deduped.columns:
                merged_deduped['Pos_Scraped'] = merged_deduped.get('Pos', '')

            updated_rows = 0

            # Match position by PlayerID first
            if 'PlayerID' in players_df.columns and 'PlayerID' in merged_deduped.columns:
                pos_lookup = players_df[['PlayerID', 'Pos']].dropna(subset=['PlayerID'])
                pos_lookup = pos_lookup[pos_lookup['PlayerID'].astype(str).str.strip() != '']
                pos_lookup = pos_lookup.drop_duplicates(subset=['PlayerID'])

                # Left join position by PlayerID
                merged = merged_deduped.merge(pos_lookup, on='PlayerID', how='left', suffixes=('', '_from_players'))

                # Update position where roster position is available
                if 'Pos_from_players' in merged.columns:
                    mask_update = merged['Pos_from_players'].notna() & (merged['Pos_from_players'] != merged['Pos'])
                    updated_rows = int(mask_update.sum())
                    merged['Pos'] = merged['Pos_from_players'].fillna(merged['Pos'])
                    merged.drop(columns=['Pos_from_players'], inplace=True)
                    merged_deduped = merged

            # Fallback: Match position by player name if ID match yielded no updates
            if updated_rows == 0 and 'Player' in players_df.columns and 'Player' in merged_deduped.columns:
                pos_lookup = players_df[['Player', 'Pos']].dropna(subset=['Player']).drop_duplicates(subset=['Player'])
                merged = merged_deduped.merge(pos_lookup, on='Player', how='left', suffixes=('', '_from_players'))
                if 'Pos_from_players' in merged.columns:
                    mask_update = merged['Pos_from_players'].notna() & (merged['Pos_from_players'] != merged['Pos'])
                    updated_rows = int(mask_update.sum())
                    merged['Pos'] = merged['Pos_from_players'].fillna(merged['Pos'])
                    merged.drop(columns=['Pos_from_players'], inplace=True)
                    merged_deduped = merged
    # Catch any position merge exceptions gracefully
    except Exception:
        pass

    # Standardize game date format to YYYY-MM-DD
    if 'Date' in merged.columns:
        merged['Date'] = pd.to_datetime(merged['Date'], errors='coerce', format='%m/%d/%Y')

    # Upsert cleaned game logs into SQLite database
    if not merged_deduped.empty:
        # Connect to SQLite database and prepare tables
        try:
            if 'Date' in merged.columns:
                merged['Date'] = pd.to_datetime(merged['Date'], errors='coerce').dt.strftime('%Y-%m-%d')

            db_path = os.path.join(out_dir, 'gamelogs.db')
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()

            # Schema migration check: drop old table if GameType column doesn't exist
            table_exists = cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gamelogs'").fetchone()
            if table_exists:
                columns = [r[1] for r in cur.execute("PRAGMA table_info(gamelogs)").fetchall()]
                # Drop table if schema lacks GameType column
                if 'GameType' not in columns:
                    print("Outdated database schema detected. Recreating table...")
                    cur.execute("DROP TABLE gamelogs")

            # Create gamelogs table with compound primary key for idempotent upserts
            cur.execute('''
            CREATE TABLE IF NOT EXISTS gamelogs (
                Player TEXT,
                PlayerID INTEGER,
                SummaryHref TEXT,
                GameLogsURL TEXT,
                GameType TEXT,
                Season TEXT,
                Date TEXT,
                Team TEXT,
                Opponent TEXT,
                WL TEXT,
                Status TEXT,
                Pos TEXT,
                MIN TEXT,
                PTS INTEGER,
                FGM INTEGER,
                FGA INTEGER,
                FGPercent REAL,
                TPM INTEGER,
                TPA INTEGER,
                TPPercent REAL,
                FTM INTEGER,
                FTA INTEGER,
                FTPercent REAL,
                ORB INTEGER,
                DRB INTEGER,
                REB INTEGER,
                AST INTEGER,
                STL INTEGER,
                BLK INTEGER,
                TOV INTEGER,
                PF INTEGER,
                FIC REAL,
                PRIMARY KEY (PlayerID, Date, Opponent, GameType)
            )
            ''')

            # Define exact ordered list of database columns
            db_cols = [
                'Player', 'PlayerID', 'SummaryHref', 'GameLogsURL', 'GameType', 'Season',
                'Date', 'Team', 'Opponent', 'WL', 'Status', 'Pos', 'MIN', 'PTS',
                'FGM', 'FGA', 'FGPercent', 'TPM', 'TPA', 'TPPercent', 'FTM', 'FTA',
                'FTPercent', 'ORB', 'DRB', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'FIC'
            ]
            
            # Ensure all expected columns exist in the DataFrame
            for col in db_cols:
                if col not in merged.columns:
                    merged[col] = None
                    
            # Extract data records as nested list for batch insertion
            to_write = merged[db_cols]
            records = to_write.to_numpy().tolist()
            
            # Prepare SQL statement with parameter placeholders
            placeholders = ', '.join(['?'] * len(db_cols))
            query = f"INSERT OR REPLACE INTO gamelogs ({', '.join(db_cols)}) VALUES ({placeholders})"
            
            # Execute batch upsert and commit database transaction
            cur.executemany(query, records)
            conn.commit()
            conn.close()
            print(f"Successfully upserted {len(records)} game logs into database.")
        # Catch database write exceptions
        except Exception as e:
            print(f"Error writing to database: {e}")

# Parse CLI arguments when running stats.py directly from terminal
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Scrape gamelogs from RealGM and write to gamelogs.db')
    parser.add_argument('--players', '-p', help='Path to players.csv or players.xlsx (optional)', default=None)
    parser.add_argument('--workers', '-w', type=int, default=6, help='Number of concurrent workers (default: 6)')
    parser.add_argument('--limit', '-l', type=int, default=None, help='Limit number of players to scrape (optional)')
    parser.add_argument('--season', '-s', type=str, default=None, help='Filter to specific season (e.g. 2025-26)')
    args = parser.parse_args()

    # Run main scraper pipeline with CLI arguments
    main(args.players, workers=args.workers, limit=args.limit, season_filter=args.season)