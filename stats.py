# Import core utilities for filesystem, regex, CLI args, timing, datetime, and concurrency
import os
import re
import sys
import time
from datetime import datetime, timezone, timedelta
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

# Base site URL for resolving relative player links
BASE = 'https://basketball.realgm.com'

# Master mapping of NBA franchise full names to standardized short mascot names in database
TEAM_MASCOT_MAP = {
    'Atlanta Hawks': 'Hawks',
    'Boston Celtics': 'Celtics',
    'Brooklyn Nets': 'Nets',
    'Charlotte Hornets': 'Hornets',
    'Chicago Bulls': 'Bulls',
    'Cleveland Cavaliers': 'Cavaliers',
    'Dallas Mavericks': 'Mavericks',
    'Denver Nuggets': 'Nuggets',
    'Detroit Pistons': 'Pistons',
    'Golden State Warriors': 'Warriors',
    'Houston Rockets': 'Rockets',
    'Indiana Pacers': 'Pacers',
    'Los Angeles Clippers': 'Clippers',
    'LA Clippers': 'Clippers',
    'Los Angeles Lakers': 'Lakers',
    'LA Lakers': 'Lakers',
    'Memphis Grizzlies': 'Grizzlies',
    'Miami Heat': 'Heat',
    'Milwaukee Bucks': 'Bucks',
    'Minnesota Timberwolves': 'Timberwolves',
    'New Orleans Pelicans': 'Pelicans',
    'New York Knicks': 'Knicks',
    'Oklahoma City Thunder': 'Thunder',
    'Orlando Magic': 'Magic',
    'Philadelphia 76ers': 'Sixers',
    'Philadelphia Sixers': 'Sixers',
    'Phoenix Suns': 'Suns',
    'Portland Trail Blazers': 'Trail Blazers',
    'Sacramento Kings': 'Kings',
    'San Antonio Spurs': 'Spurs',
    'Toronto Raptors': 'Raptors',
    'Utah Jazz': 'Jazz',
    'Washington Wizards': 'Wizards'
}

# Clean team name to extract standardized short mascot string
def clean_mascot(name: str) -> str:
    name = str(name).strip()
    if name in TEAM_MASCOT_MAP:
        return TEAM_MASCOT_MAP[name]
    for full, mascot in TEAM_MASCOT_MAP.items():
        if full.lower() in name.lower() or mascot.lower() == name.lower():
            return mascot
    return name

# Clean and normalize raw table header strings by removing special characters and spaces
def clean_header(col):
    if col is None:
        return ''
    s = str(col).strip()
    if not s:
        return ''
    s = re.sub(r"\s+", '_', s)
    s = re.sub(r'[^A-Za-z0-9_%]', '', s)
    return s

# Calculate NBA season format (e.g. 2026-27) based on game date
def calc_season(d):
    if pd.isna(d):
        return None
    season_end = d.year + 1 if d.month >= 8 else d.year
    return f"{season_end-1}-{str(season_end)[-2:]}"

# Map season label (e.g. '2026-27') to RealGM URL season end year (e.g. '2027')
def season_label_to_year(season_label: str) -> str:
    if not season_label:
        return 'All'
    m = re.match(r"^(\d{4})-(\d{2})$", season_label.strip())
    if m:
        y1, y2 = m.groups()
        century = y1[:2]
        return f"{century}{y2}"
    return season_label.strip()

# Construct the RealGM game logs URL for a player, optionally targeting a specific season year
def build_gamelogs_url(summary_url: str, season_year: str = 'All') -> str:
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

    target_segment = f"/GameLogs/{pid}/NBA/{season_year}"
    gamelogs = re.sub(r"/Summary/\d+", target_segment, summary_url)
    if '/GameLogs/' not in gamelogs:
        base_player = re.sub(r"/Summary/\d+", "", summary_url)
        gamelogs = base_player.rstrip('/') + target_segment

    return gamelogs

# Fetch webpage HTML using standard requests with automated retries and timeout
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

# Batch fetch URLs using curl_cffi with Chrome 120 TLS fingerprinting to bypass anti-bot protections
def fetch_htmls_curl_cffi(urls: list[str], timeout: int = 20) -> list[str]:
    try:
        from curl_cffi import requests as cffi_requests
        session = cffi_requests.Session(impersonate="chrome120")
        results = []
        for url in urls:
            try:
                resp = session.get(url, timeout=timeout)
                if resp.status_code == 200:
                    results.append(resp.text)
                else:
                    results.append('')
            except Exception:
                results.append('')
        return results
    except Exception:
        return []

# Fallback headless Chrome scraper using Selenium for JavaScript-rendered game log tables
def fetch_htmls_selenium(urls: list[str], timeout: int = 30) -> list[str]:
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

# Parse game logs table HTML into a structured pandas DataFrame
def parse_gamelogs_table(html: str) -> pd.DataFrame:
    soup = BeautifulSoup(html, 'lxml')

    table = soup.select_one('div.fixed-table-body table')
    if not table:
        table = soup.select_one('table[data-toggle="table"]')
    if not table:
        tables = soup.find_all('table')
        if tables:
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

# Scrape boxscores for a specific date directly from RealGM scoreboard
def scrape_boxscores_for_date(date_str: str, session=None) -> pd.DataFrame:
    if session is None:
        try:
            from curl_cffi import requests as cffi_requests
            session = cffi_requests.Session(impersonate='chrome120')
        except ImportError:
            session = requests.Session()

    url = f"https://basketball.realgm.com/nba/scores/{date_str}"
    print(f"Fetching scoreboard for {date_str}: {url}")
    try:
        r = session.get(url, timeout=15)
        if r.status_code != 200:
            print(f"Failed to fetch scoreboard for {date_str} (status {r.status_code})")
            return pd.DataFrame()
    except Exception as e:
        print(f"Network error fetching scoreboard for {date_str}: {e}")
        return pd.DataFrame()

    soup = BeautifulSoup(r.text, 'lxml')
    box_links = list(dict.fromkeys([a['href'] for a in soup.find_all('a', href=re.compile(r'/nba/boxscore/'))]))

    if not box_links:
        print(f"No completed boxscores found on RealGM for {date_str}.")
        return pd.DataFrame()

    print(f"Found {len(box_links)} completed boxscores for {date_str}. Parsing games...")
    parsed_rows = []

    dt = datetime.strptime(date_str, '%Y-%m-%d')
    season = calc_season(dt)

    # Classify GameType based on NBA calendar schedule boundaries
    game_type = 'Regular Season'
    if season == '2026-27':
        if dt < datetime(2026, 10, 20):
            game_type = 'Preseason'
        elif dt > datetime(2027, 4, 11):
            game_type = 'Playoffs'
    else:
        if dt.month in [9, 10] and dt.day < 20:
            game_type = 'Preseason'
        elif dt.month in [4, 5, 6] and dt.day > 15:
            game_type = 'Playoffs'

    for b_link in box_links:
        full_url = f"https://basketball.realgm.com{b_link}" if b_link.startswith('/') else b_link
        try:
            r_box = session.get(full_url, timeout=15)
            if r_box.status_code != 200:
                continue
        except Exception:
            continue

        soup_box = BeautifulSoup(r_box.text, 'lxml')

        # Extract linescore table to determine final game score and W/L status
        t0 = soup_box.find('table')
        team_scores = []
        if t0:
            for tr in t0.find_all('tr')[1:]:
                cells = [td.text.strip() for td in tr.find_all(['th', 'td'])]
                if len(cells) >= 6:
                    team_str = cells[0].split('(')[0].strip()
                    try:
                        final_score = int(cells[-1])
                    except Exception:
                        final_score = 0
                    team_scores.append((team_str, final_score))

        # Locate player statistics tables for both teams
        player_tables = []
        for t in soup_box.find_all('table'):
            th_texts = [th.text.strip() for th in t.find_all('th')]
            if 'Player' in th_texts and 'Min' in th_texts and 'FGM-A' in th_texts:
                prev = t.find_previous(['h2', 'h3'])
                t_name = prev.text.strip() if prev else ''
                player_tables.append((t_name, t))

        if len(player_tables) == 2:
            team1_name, t1 = player_tables[0]
            team2_name, t2 = player_tables[1]

            mascot1 = clean_mascot(team1_name)
            mascot2 = clean_mascot(team2_name)

            wl1, wl2 = 'W', 'L'
            if len(team_scores) >= 2:
                s1 = team_scores[0][1]
                s2 = team_scores[1][1]
                if s1 > s2:
                    wl1, wl2 = 'W', 'L'
                else:
                    wl1, wl2 = 'L', 'W'

            def parse_team_box(t, team, opp, wl):
                t_rows = []
                for tr in t.find_all('tr'):
                    a = tr.find('a')
                    if not a or '/player/' not in a.get('href', ''):
                        continue
                    p_name = a.text.strip()
                    p_href = a['href']
                    pid_m = re.search(r'/Summary/(\d+)', p_href)
                    pid = int(pid_m.group(1)) if pid_m else None

                    tds = [td.text.strip() for td in tr.find_all('td')]
                    if len(tds) < 18:
                        continue

                    status = tds[2]
                    pos = tds[3]
                    # Normalize minutes format by stripping leading zero on single digit minutes (e.g. 06:20 -> 6:20)
                    mins = re.sub(r'^0(\d:)', r'\1', tds[4].strip())

                    def split_stat(s):
                        parts = s.split('-')
                        if len(parts) == 2:
                            try:
                                m = int(parts[0])
                                att = int(parts[1])
                                pct = round(m / att, 3) if att > 0 else 0.0
                                return m, att, pct
                            except Exception:
                                pass
                        return 0, 0, 0.0

                    fgm, fga, fg_pct = split_stat(tds[5])
                    tpm, tpa, tp_pct = split_stat(tds[6])
                    ftm, fta, ft_pct = split_stat(tds[7])

                    def to_int(v):
                        try:
                            return int(v)
                        except Exception:
                            return 0

                    def to_float(v):
                        try:
                            return float(v)
                        except Exception:
                            return 0.0

                    fic = to_float(tds[8])
                    orb = to_int(tds[9])
                    drb = to_int(tds[10])
                    reb = to_int(tds[11])
                    ast = to_int(tds[12])
                    pf = to_int(tds[13])
                    stl = to_int(tds[14])
                    blk = to_int(tds[15])
                    tov = to_int(tds[16])
                    pts = to_int(tds[17])

                    t_rows.append({
                        'Player': p_name,
                        'PlayerID': pid,
                        'SummaryHref': p_href,
                        'GameLogsURL': f"https://basketball.realgm.com{p_href.replace('/Summary/', '/GameLogs/')}/NBA/All",
                        'GameType': game_type,
                        'Season': season,
                        'Date': date_str,
                        'Team': team,
                        'Opponent': opp,
                        'WL': wl,
                        'Status': status,
                        'Pos': pos,
                        'MIN': mins,
                        'PTS': pts,
                        'FGM': fgm,
                        'FGA': fga,
                        'FGPercent': fg_pct,
                        'TPM': tpm,
                        'TPA': tpa,
                        'TPPercent': tp_pct,
                        'FTM': ftm,
                        'FTA': fta,
                        'FTPercent': ft_pct,
                        'ORB': orb,
                        'DRB': drb,
                        'REB': reb,
                        'AST': ast,
                        'STL': stl,
                        'BLK': blk,
                        'TOV': tov,
                        'PF': pf,
                        'FIC': fic
                    })
                return t_rows

            parsed_rows.extend(parse_team_box(t1, mascot1, mascot2, wl1))
            parsed_rows.extend(parse_team_box(t2, mascot2, mascot1, wl2))

    return pd.DataFrame(parsed_rows)

# Scrape game logs for a specific player (single season or all history)
def process_player(player_name: str, summary_href: str, out_dir: str, season_year: str = 'All') -> pd.DataFrame:
    gamelogs_url = build_gamelogs_url(summary_href, season_year=season_year)
    if not gamelogs_url:
        return pd.DataFrame()

    if season_year != 'All':
        urls = [gamelogs_url]
        game_types = ['Regular Season']
    else:
        suffixes = ['Reg', 'Playoffs', 'Play-In', 'Preseason']
        game_types = ['Regular Season', 'Playoffs', 'Play-In', 'Preseason']
        urls = [f"{gamelogs_url}/{s}" for s in suffixes]

    htmls = fetch_htmls_curl_cffi(urls)
    if not any(htmls):
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

    # Filter out historical logs prior to 2015-16 season kickoff if crawling full history
    if season_year == 'All':
        df = df[df['Date_Parsed'] >= datetime(2015, 10, 27)].copy()
        if df.empty:
            return pd.DataFrame()

    df['Season'] = df['Date_Parsed'].apply(calc_season)

    # Enforce official 2026-27 schedule (Tuesday, October 20, 2026 to Sunday, April 11, 2027)
    mask_early_2026 = (df['Season'] == '2026-27') & (df['GameType'] == 'Regular Season') & (df['Date_Parsed'] < datetime(2026, 10, 20))
    df.loc[mask_early_2026, 'GameType'] = 'Preseason'

    mask_late_2026 = (df['Season'] == '2026-27') & (df['GameType'] == 'Regular Season') & (df['Date_Parsed'] > datetime(2027, 4, 11))
    df.loc[mask_late_2026, 'GameType'] = 'Playoffs'

    df.drop(columns=['Date_Parsed'], inplace=True, errors='ignore')

    df.insert(0, 'Player', player_name)
    m = re.search(r"/Summary/(\d+)", summary_href)
    pid = int(m.group(1)) if m else None
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

# Merge verified player positions from players roster file
def merge_player_positions(merged: pd.DataFrame, out_dir: str = None) -> pd.DataFrame:
    out_dir = out_dir or os.path.dirname(os.path.abspath(__file__))
    players_csv = os.path.join(out_dir, 'players.csv')
    players_xlsx = os.path.join(out_dir, 'players.xlsx')
    players_file = players_csv if os.path.exists(players_csv) else players_xlsx

    if not os.path.exists(players_file):
        return merged

    try:
        players_df = pd.read_csv(players_file) if players_file.endswith('.csv') else pd.read_excel(players_file)
        if 'Pos' not in players_df.columns:
            return merged

        if 'PlayerID' not in players_df.columns and 'PlayerHref' in players_df.columns:
            players_df['PlayerID'] = players_df['PlayerHref'].astype(str).str.extract(r'/Summary/(\d+)', expand=False).fillna('')

        if 'PlayerID' in players_df.columns and 'PlayerID' in merged.columns:
            players_df['PlayerID_str'] = players_df['PlayerID'].astype(str).str.strip()
            merged['PlayerID_str'] = merged['PlayerID'].astype(str).str.strip()

            pos_lookup = players_df[['PlayerID_str', 'Pos']].dropna(subset=['PlayerID_str'])
            pos_lookup = pos_lookup[pos_lookup['PlayerID_str'] != ''].drop_duplicates(subset=['PlayerID_str'])

            joined = merged.merge(pos_lookup, on='PlayerID_str', how='left', suffixes=('', '_from_players'))
            if 'Pos_from_players' in joined.columns:
                joined['Pos'] = joined['Pos_from_players'].fillna(joined['Pos'])
                joined.drop(columns=['Pos_from_players', 'PlayerID_str'], inplace=True, errors='ignore')
                return joined

        merged.drop(columns=['PlayerID_str'], inplace=True, errors='ignore')
    except Exception:
        pass
    return merged

# Upsert clean game logs into SQLite database with compound primary key
def upsert_to_database(merged: pd.DataFrame, out_dir: str = None) -> int:
    if merged.empty:
        print("No game logs to write to database.")
        return 0

    out_dir = out_dir or os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(out_dir, 'gamelogs.db')

    # Standardize column headers and format date to YYYY-MM-DD
    merged.columns = [clean_header(c) for c in merged.columns]
    if 'Date' in merged.columns:
        merged['Date'] = pd.to_datetime(merged['Date'], errors='coerce').dt.strftime('%Y-%m-%d')

    merged = merge_player_positions(merged, out_dir=out_dir)
    merged_deduped = merged.drop_duplicates(subset=['PlayerID', 'Date', 'Opponent', 'GameType']).reset_index(drop=True)

    db_cols = [
        'Player', 'PlayerID', 'SummaryHref', 'GameLogsURL', 'GameType', 'Season',
        'Date', 'Team', 'Opponent', 'WL', 'Status', 'Pos', 'MIN', 'PTS',
        'FGM', 'FGA', 'FGPercent', 'TPM', 'TPA', 'TPPercent', 'FTM', 'FTA',
        'FTPercent', 'ORB', 'DRB', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'FIC'
    ]

    for col in db_cols:
        if col not in merged_deduped.columns:
            merged_deduped[col] = None

    to_write = merged_deduped[db_cols]
    records = to_write.to_numpy().tolist()

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

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

    placeholders = ', '.join(['?'] * len(db_cols))
    query = f"INSERT OR REPLACE INTO gamelogs ({', '.join(db_cols)}) VALUES ({placeholders})"

    cur.executemany(query, records)
    conn.commit()
    conn.close()

    print(f"Successfully upserted {len(records)} game logs into {db_path}.")
    return len(records)

# Determine missing sync dates using Arizona local time (MST, UTC-7) and database MAX(Date)
def get_missing_sync_dates(db_path: str, max_lookback_days: int = 5) -> list[str]:
    # Arizona Standard Time (UTC-7, no Daylight Saving Time)
    az_tz = timezone(timedelta(hours=-7))
    now_az = datetime.now(az_tz)
    yesterday_az = now_az.date() - timedelta(days=1)

    if not os.path.exists(db_path):
        return [yesterday_az.strftime('%Y-%m-%d')]

    max_date_str = None
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        res = cur.execute("SELECT MAX(Date) FROM gamelogs").fetchone()
        max_date_str = res[0] if res else None
        conn.close()
    except Exception:
        max_date_str = None

    if not max_date_str:
        return [yesterday_az.strftime('%Y-%m-%d')]

    try:
        max_date = datetime.strptime(max_date_str, '%Y-%m-%d').date()
    except ValueError:
        return [yesterday_az.strftime('%Y-%m-%d')]

    dates = []
    # If the database is already current up to yesterday, refresh yesterday to capture any late official updates
    if max_date >= yesterday_az:
        dates = [yesterday_az.strftime('%Y-%m-%d')]
    else:
        # Collect missing dates from the day after MAX(Date) up to yesterday
        curr = max_date + timedelta(days=1)
        earliest_allowed = yesterday_az - timedelta(days=max_lookback_days)
        if curr < earliest_allowed:
            curr = earliest_allowed
        while curr <= yesterday_az:
            dates.append(curr.strftime('%Y-%m-%d'))
            curr += timedelta(days=1)

    return dates

# Fast incremental daily stats sync using RealGM daily scoreboard boxscores
def sync_daily_stats(target_dates: list[str] = None, out_dir: str = None) -> int:
    out_dir = out_dir or os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(out_dir, 'gamelogs.db')

    if not target_dates:
        target_dates = get_missing_sync_dates(db_path)

    print(f"--- Starting daily incremental stats refresh for dates: {target_dates} ---")
    all_frames = []

    try:
        from curl_cffi import requests as cffi_requests
        session = cffi_requests.Session(impersonate='chrome120')
    except ImportError:
        session = requests.Session()

    for date_str in target_dates:
        df_day = scrape_boxscores_for_date(date_str, session=session)
        if not df_day.empty:
            all_frames.append(df_day)

    if not all_frames:
        print("No new game logs collected for target date(s). Database is up to date.")
        return 0

    combined = pd.concat(all_frames, ignore_index=True)
    count = upsert_to_database(combined, out_dir=out_dir)
    return count

# Fallback player-by-player scraper orchestration for specific season or full historical backfill
def sync_players_scrape(players_file: str = None, workers: int = 6, limit: int = None, season_filter: str = None, all_history: bool = False):
    out_dir = os.path.dirname(os.path.abspath(__file__))
    if not players_file:
        default_csv = os.path.join(out_dir, 'players.csv')
        default_xlsx = os.path.join(out_dir, 'players.xlsx')
        players_file = default_csv if os.path.exists(default_csv) else default_xlsx

    if not os.path.exists(players_file):
        print(f"File not found: {players_file}")
        return

    try:
        players_df = pd.read_csv(players_file) if players_file.endswith('.csv') else pd.read_excel(players_file)
    except Exception as e:
        print(f"Error reading {players_file}: {e}")
        return

    if 'PlayerHref' not in players_df.columns and 'Player' not in players_df.columns:
        print("Required columns missing from players file.")
        return

    season_year = 'All' if all_history else (season_label_to_year(season_filter) if season_filter else '2027')

    def player_row_to_args(row, idx):
        player = row.get('Player', '')
        href = row.get('PlayerHref', '')
        if not href and isinstance(row.get('Player', ''), str):
            if row.get('Player', '').startswith('http') or row.get('Player', '').startswith('/'):
                href = row.get('Player')
        if not href:
            return None
        return (player or f'player_{idx}', href, out_dir, season_year)

    player_args = [player_row_to_args(row, idx) for idx, row in players_df.iterrows()]
    player_args = [a for a in player_args if a is not None]

    if limit:
        player_args = player_args[:limit]
        print(f"Limiting scrape to first {limit} players.")

    all_frames = []
    max_workers = min(workers, len(player_args)) if player_args else 1
    total_players = len(player_args)
    completed = 0

    mode_desc = f"season {season_year}" if season_year != 'All' else "full career history (2015-present)"
    print(f"Starting player stats collection for {total_players} players ({mode_desc}) with {max_workers} concurrent workers...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_player, *args): args[0] for args in player_args}
        for future in as_completed(futures):
            p_name = futures[future]
            completed += 1
            try:
                df = future.result()
                if not df.empty:
                    if season_filter and season_year == 'All':
                        df = df[df['Season'] == season_filter]
                    if not df.empty:
                        all_frames.append(df)
                        print(f"[{completed}/{total_players}] {p_name}: {len(df)} games collected")
                    else:
                        print(f"[{completed}/{total_players}] {p_name}: 0 games for season {season_filter}")
                else:
                    print(f"[{completed}/{total_players}] {p_name}: 0 games found")
            except Exception as e:
                print(f"[{completed}/{total_players}] {p_name}: Error {e}")

    if not all_frames:
        print("No games collected to write.")
        return

    combined = pd.concat(all_frames, ignore_index=True)
    upsert_to_database(combined, out_dir=out_dir)

# Main entry point for CLI execution
def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='NBA Game Logs scraper: Fast daily incremental boxscore refresh (default) or player-by-player sync.'
    )
    parser.add_argument('--date', '-d', type=str, default=None, help='Sync boxscores for specific date (YYYY-MM-DD)')
    parser.add_argument('--days', type=int, default=None, help='Sync boxscores for the last N days')
    parser.add_argument('--season', '-s', type=str, default=None, help='Sync specific season for all players (e.g. 2026-27)')
    parser.add_argument('--all-history', action='store_true', help='Perform full historical backfill from 2015 for all players (slow)')
    parser.add_argument('--players', '-p', help='Path to players.csv or players.xlsx (optional)', default=None)
    parser.add_argument('--workers', '-w', type=int, default=6, help='Number of concurrent workers for player sync (default: 6)')
    parser.add_argument('--limit', '-l', type=int, default=None, help='Limit number of players scraped in player mode (optional)')

    args = parser.parse_args()

    # If full history or season player scrape requested, invoke player sync
    if args.all_history or args.season:
        sync_players_scrape(
            players_file=args.players,
            workers=args.workers,
            limit=args.limit,
            season_filter=args.season,
            all_history=args.all_history
        )
    # If specific date or range of days requested for daily boxscores
    elif args.date:
        sync_daily_stats(target_dates=[args.date])
    elif args.days:
        az_tz = timezone(timedelta(hours=-7))
        yesterday_az = datetime.now(az_tz).date() - timedelta(days=1)
        target_dates = [(yesterday_az - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(args.days)][::-1]
        sync_daily_stats(target_dates=target_dates)
    # Default execution: Smart incremental daily sync based on Arizona time & SQLite state
    else:
        sync_daily_stats()

if __name__ == '__main__':
    main()