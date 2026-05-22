import os
import re
import sys
import time
from datetime import datetime
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import requests
import sqlite3
from bs4 import BeautifulSoup
from bisect import bisect_right
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def clean_header(col):
    if col is None:
        return ''
    s = str(col).strip()
    if not s:
        return ''
    s = re.sub(r"\s+", '_', s)
    s = re.sub(r'[^A-Za-z0-9_%]', '', s)
    return s

# Base site URL for resolving relative player links
BASE = 'https://basketball.realgm.com'

def build_gamelogs_url(summary_url: str) -> str:
    if not summary_url:
        return ''
    if summary_url.startswith('/'):
        summary_url = urljoin(BASE, summary_url)

    m = re.search(r"/Summary/(\d+)", summary_url)
    if not m:
        parts = summary_url.rstrip('/').split('/')
        if parts and parts[-1].isdigit():
            pid = parts[-1]
        else:
            return ''
    else:
        pid = m.group(1)

    gamelogs = re.sub(r"/Summary/\d+", f"/GameLogs/{pid}/NBA/All", summary_url)
    if '/GameLogs/' not in gamelogs:
        base_player = re.sub(r"/Summary/\d+", "", summary_url)
        gamelogs = base_player.rstrip('/') + f"/GameLogs/{pid}/NBA/All"

    return gamelogs

def fetch_html(url: str, headers=None, timeout=15) -> str:
    headers = headers or {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    tries = 3
    for attempt in range(1, tries + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                return resp.text
        except Exception:
            pass
        time.sleep(1)
    return ''

def fetch_htmls_selenium(urls: list[str], timeout: int = 30) -> list[str]:
    chrome_options = Options()
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )

    driver = None
    results = []
    try:
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
        driver.set_page_load_timeout(timeout)
        driver.implicitly_wait(2)

        for url in urls:
            try:
                driver.get(url)
                try:
                    wait = WebDriverWait(driver, 5)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
                except TimeoutException:
                    pass
                results.append(driver.page_source)
            except Exception:
                results.append('')
            time.sleep(0.5)
    except WebDriverException:
        results = [''] * len(urls)
    finally:
        try:
            if driver:
                driver.quit()
        except Exception:
            pass
    return results

def parse_gamelogs_table(html: str) -> pd.DataFrame:
    soup = BeautifulSoup(html, 'lxml')

    table = soup.select_one('div.fixed-table-body table')
    if not table:
        table = soup.select_one('table[data-toggle="table"]')
    
    if not table:
        tables = soup.find_all('table')
        if tables:
            # find table with the most rows
            table = max(tables, key=lambda t: len(t.find_all('tr')))
        else:
            table = None
            
    if not table:
        return pd.DataFrame()

    headers = []
    thead = table.find('thead')
    if thead:
        for th in thead.find_all('th'):
            text = th.get_text(strip=True)
            headers.append(text)
    if not headers:
        tr0 = table.find('tr')
        cols = len(tr0.find_all(['td','th'])) if tr0 else 0
        headers = [f'col_{i}' for i in range(cols)]

    rows = []
    tbody = table.find('tbody')
    if not tbody:
        return pd.DataFrame()

    for tr in tbody.find_all('tr'):
        cells = tr.find_all('td')
        if not cells:
            continue
        row = {}
        for i, td in enumerate(cells):
            key = headers[i] if i < len(headers) else f'col_{i}'
            a = td.find('a')
            if a and a.get('href'):
                row[key] = a.get_text(strip=True)
                href = a['href']
                row[f'{key}Href'] = urljoin(BASE, href) if href.startswith('/') else href
            else:
                row[key] = td.get_text(strip=True)
        rows.append(row)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    return df

def process_player(player_name: str, summary_href: str, out_dir: str) -> pd.DataFrame:
    gamelogs_url = build_gamelogs_url(summary_href)
    if not gamelogs_url:
        return pd.DataFrame()
    
    suffixes = ['Reg', 'Playoffs', 'Play-In', 'Preseason']
    game_types = ['Regular Season', 'Playoffs', 'Play-In', 'Preseason']
    urls = [f"{gamelogs_url}/{s}" for s in suffixes]
    
    htmls = fetch_htmls_selenium(urls)
    
    dfs = []
    for gt, html in zip(game_types, htmls):
        if not html:
            continue
        df_parsed = parse_gamelogs_table(html)
        if df_parsed.empty:
            continue
        df_parsed['GameType'] = gt
        dfs.append(df_parsed)
        
    if not dfs:
        return pd.DataFrame()
        
    df = pd.concat(dfs, ignore_index=True)
    
    date_col = None
    for c in df.columns:
        if str(c).strip().lower() == 'date':
            date_col = c
            break
    if date_col is None:
        date_col = df.columns[0]

    parsed_dates = pd.to_datetime(df[date_col], errors='coerce', format='%m/%d/%Y')
    df['Date_Parsed'] = parsed_dates
    
    # Keep only dates after the 2015-16 season starts (2015-10-27)
    df = df[df['Date_Parsed'] >= datetime(2015, 10, 27)].copy()
    if df.empty:
        return pd.DataFrame()
        
    def calc_season(d):
        if pd.isna(d):
            return None
        season_end = d.year + 1 if d.month >= 8 else d.year
        return f"{season_end-1}-{str(season_end)[-2:]}"
        
    df['Season'] = df['Date_Parsed'].apply(calc_season)
    df.drop(columns=['Date_Parsed'], inplace=True, errors='ignore')

    df.insert(0, 'Player', player_name)
    m = re.search(r"/Summary/(\d+)", summary_href)
    pid = m.group(1) if m else ''
    df.insert(1, 'PlayerID', pid)
    df.insert(2, 'SummaryHref', summary_href)
    df.insert(3, 'GameLogsURL', gamelogs_url)
    
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

    int_cols = ['PTS', 'FGM', 'FGA', 'TPM', 'TPA', 'FTM', 'FTA', 'ORB', 'DRB', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF']
    for c in int_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype(int)
            
    float_cols = ['FGPercent', 'TPPercent', 'FTPercent', 'FIC']
    for c in float_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0.0).astype(float)

    return df

def main(players_excel: str = None):
    players_excel = players_excel or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'players.xlsx')
    if not os.path.exists(players_excel):
        return

    out_dir = os.path.dirname(os.path.abspath(__file__))

    players_df = pd.read_excel(players_excel)
    if 'PlayerHref' not in players_df.columns and 'Player' not in players_df.columns:
        return

    def player_row_to_args(row, idx):
        player = row.get('Player', '')
        href = row.get('PlayerHref', '')
        if not href and isinstance(row.get('Player', ''), str):
            if row.get('Player', '').startswith('http') or row.get('Player', '').startswith('/'):
                href = row.get('Player')
        if not href:
            return None
        return (player or f'player_{idx}', href, out_dir)
    
    player_args = [player_row_to_args(row, idx) for idx, row in players_df.iterrows()]
    player_args = [a for a in player_args if a is not None]
    
    all_frames = []
    # Reduce workers to avoid spawning too many browser instances
    max_workers = min(2, len(player_args))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_player, *args) for args in player_args]
        for future in as_completed(futures):
            try:
                df = future.result()
                if not df.empty:
                    all_frames.append(df)
            except Exception:
                pass

    if not all_frames:
        return

    combined_new = pd.concat(all_frames, ignore_index=True)
    merged = combined_new

    try:
        merged_deduped = merged.drop_duplicates().reset_index(drop=True)
    except Exception:
        merged_deduped = merged.copy() if hasattr(merged, 'copy') else merged

    merged.columns = [clean_header(c) for c in merged.columns]

    try:
        if 'Pos' in players_df.columns:
            if 'PlayerID' not in players_df.columns and 'PlayerHref' in players_df.columns:
                players_df['PlayerID'] = players_df['PlayerHref'].astype(str).str.extract(r'/Summary/(\d+)', expand=False).fillna('')

            if 'PlayerID' in players_df.columns:
                players_df['PlayerID'] = players_df['PlayerID'].astype(str).str.strip()

            if 'PlayerID' in merged_deduped.columns:
                merged_deduped['PlayerID'] = merged_deduped['PlayerID'].astype(str).str.strip()

            if 'Pos_Scraped' not in merged_deduped.columns:
                merged_deduped['Pos_Scraped'] = merged_deduped.get('Pos', '')

            updated_rows = 0

            if 'PlayerID' in players_df.columns and 'PlayerID' in merged_deduped.columns:
                pos_lookup = players_df[['PlayerID', 'Pos']].dropna(subset=['PlayerID'])
                pos_lookup = pos_lookup[pos_lookup['PlayerID'].astype(str).str.strip() != '']
                pos_lookup = pos_lookup.drop_duplicates(subset=['PlayerID'])

                merged = merged_deduped.merge(pos_lookup, on='PlayerID', how='left', suffixes=('', '_from_players'))

                if 'Pos_from_players' in merged.columns:
                    mask_update = merged['Pos_from_players'].notna() & (merged['Pos_from_players'] != merged['Pos'])
                    updated_rows = int(mask_update.sum())
                    merged['Pos'] = merged['Pos_from_players'].fillna(merged['Pos'])
                    merged.drop(columns=['Pos_from_players'], inplace=True)
                    merged_deduped = merged

            if updated_rows == 0 and 'Player' in players_df.columns and 'Player' in merged_deduped.columns:
                pos_lookup = players_df[['Player', 'Pos']].dropna(subset=['Player']).drop_duplicates(subset=['Player'])
                merged = merged_deduped.merge(pos_lookup, on='Player', how='left', suffixes=('', '_from_players'))
                if 'Pos_from_players' in merged.columns:
                    mask_update = merged['Pos_from_players'].notna() & (merged['Pos_from_players'] != merged['Pos'])
                    updated_rows = int(mask_update.sum())
                    merged['Pos'] = merged['Pos_from_players'].fillna(merged['Pos'])
                    merged.drop(columns=['Pos_from_players'], inplace=True)
                    merged_deduped = merged
    except Exception:
        pass

    if 'Date' in merged.columns:
        merged['Date'] = pd.to_datetime(merged['Date'], errors='coerce', format='%m/%d/%Y')

    if not merged_deduped.empty:
        try:
            if 'Date' in merged.columns:
                merged['Date'] = pd.to_datetime(merged['Date'], errors='coerce').dt.strftime('%Y-%m-%d')

            db_path = os.path.join(out_dir, 'gamelogs.db')
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()

            # Schema migration check: drop old table if GameType doesn't exist
            table_exists = cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gamelogs'").fetchone()
            if table_exists:
                columns = [r[1] for r in cur.execute("PRAGMA table_info(gamelogs)").fetchall()]
                if 'GameType' not in columns:
                    print("Outdated database schema detected. Recreating table...")
                    cur.execute("DROP TABLE gamelogs")

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

            db_cols = [
                'Player', 'PlayerID', 'SummaryHref', 'GameLogsURL', 'GameType', 'Season',
                'Date', 'Team', 'Opponent', 'WL', 'Status', 'Pos', 'MIN', 'PTS',
                'FGM', 'FGA', 'FGPercent', 'TPM', 'TPA', 'TPPercent', 'FTM', 'FTA',
                'FTPercent', 'ORB', 'DRB', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'FIC'
            ]
            
            for col in db_cols:
                if col not in merged.columns:
                    merged[col] = None
                    
            to_write = merged[db_cols]
            records = to_write.to_numpy().tolist()
            
            placeholders = ', '.join(['?'] * len(db_cols))
            query = f"INSERT OR REPLACE INTO gamelogs ({', '.join(db_cols)}) VALUES ({placeholders})"
            
            cur.executemany(query, records)
            conn.commit()
            conn.close()
            print(f"Successfully upserted {len(records)} game logs into database.")
        except Exception as e:
            print(f"Error writing to database: {e}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Scrape gamelogs from RealGM and write to gamelogs.db')
    parser.add_argument('--players', '-p', help='Path to players.xlsx (optional)', default=None)
    args = parser.parse_args()

    main(args.players)