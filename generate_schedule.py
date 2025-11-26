import argparse
import pandas as pd
import time
import requests
from bs4 import BeautifulSoup
import re
from typing import Optional, List
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"

DEFAULT_TEAM_REFS = [
    'Atlanta-Hawks','Boston-Celtics','Brooklyn-Nets','Charlotte-Hornets','Chicago-Bulls',
    'Cleveland-Cavaliers','Dallas-Mavericks','Denver-Nuggets','Detroit-Pistons','Golden-State-Warriors',
    'Houston-Rockets','Indiana-Pacers','Los-Angeles-Clippers','Los-Angeles-Lakers','Memphis-Grizzlies',
    'Miami-Heat','Milwaukee-Bucks','Minnesota-Timberwolves','New-Orleans-Pelicans','New-York-Knicks',
    'Oklahoma-City-Thunder','Orlando-Magic','Philadelphia-Sixers','Phoenix-Suns','Portland-Trail-Blazers',
    'Sacramento-Kings','San-Antonio-Spurs','Toronto-Raptors','Utah-Jazz','Washington-Wizards'
]

def build_initial_df(year: int, team_refs: list = None) -> pd.DataFrame:
    team_refs = team_refs or DEFAULT_TEAM_REFS
    base = 'https://basketball.realgm.com/nba/teams/{team_ref}/1/Schedule/{year}'
    rows = [{'TeamRef': tr, 'Schedule': base.format(team_ref=tr, year=year)} for tr in team_refs]
    return pd.DataFrame(rows)

def extract_opponent_text(td):
    a = td.find('a')
    if a and a.text:
        return a.text.strip()
    txt = td.get_text(separator=' ', strip=True)
    for marker in ['v.', '@']:
        if txt.startswith(marker):
            return txt[len(marker):].strip()
    return txt

def extract_team_from_href(href: str) -> str:
    if not isinstance(href, str):
        return ''
    m = re.search(r"/teams/([^/]+)/", href)
    if m:
        return m.group(1)
    return href

def normalize_opponent_text(opp: str, team_refs: list) -> str:
    if not isinstance(opp, str):
        return ''
    s_norm = re.sub(r"\s+", " ", opp.strip()).strip()
    s_lower = s_norm.lower()
    best = None
    best_score = 0
    for tr in team_refs:
        tr_norm = tr.replace('-', ' ').lower()
        if s_lower == tr_norm:
            return tr
        if s_lower in tr_norm:
            score = len(s_lower)
            if score > best_score:
                best = tr
                best_score = score
        elif tr_norm in s_lower:
            score = len(tr_norm)
            if score > best_score:
                best = tr
                best_score = score
    if best:
        return best
    return '-'.join([w.capitalize() for w in s_norm.split()])

def fetch_html_requests(session: requests.Session, url: str, timeout: int = 15) -> str:
    try:
        r = session.get(url, timeout=timeout)
        r.raise_for_status()
        return r.text
    except Exception:
        return ''



def scrape_schedules(season_df: pd.DataFrame, year: int, output_xlsx: str, *,
                     verbose: bool = False,
                     limit: Optional[int] = None, save_initial: Optional[str] = None):
    session = requests.Session()
    session.headers.update({'User-Agent': USER_AGENT})
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["HEAD", "GET", "OPTIONS"])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('https://', adapter)
    session.mount('http://', adapter)

    if 'TeamHref' not in season_df.columns and 'TeamRef' in season_df.columns:
        season_df = season_df.rename(columns={'TeamRef': 'TeamHref'})

    if save_initial:
        season_df.to_excel(save_initial, index=False)

    rows = []
    team_refs = list(season_df['TeamHref'].dropna().unique()) if 'TeamHref' in season_df.columns else []
    if limit:
        iterable = list(season_df.iterrows())[:limit]
    else:
        iterable = season_df.iterrows()

    for idx, row in iterable:
        team_href = row.get('TeamHref')
        schedule_url = row.get('Schedule')
        if pd.isna(schedule_url) or not schedule_url:
            continue
        if schedule_url.startswith('/'):
            schedule_url = 'https://basketball.realgm.com' + schedule_url

        html = ''
        html = fetch_html_requests(session, schedule_url)

        if not html:
            time.sleep(1)
            continue

        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table', attrs={'data-toggle': 'table'}) or soup.find('table', class_='table')
        if not table:
            time.sleep(1)
            continue
        tbody = table.find('tbody')
        if not tbody:
            time.sleep(1)
            continue

        for tr in tbody.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) < 2:
                continue
            date_td = tds[0]
            opp_td = tds[1]
            date_text = date_td.get_text(separator=' ', strip=True)
            a_date = date_td.find('a')
            if a_date and a_date.text:
                date_text = a_date.text.strip()
            opp_text = extract_opponent_text(opp_td)
            rows.append({'TeamHref': team_href, 'ScheduleURL': schedule_url, 'Date': date_text, 'Opponent': opp_text})

        time.sleep(0.8)

    out_df = pd.DataFrame(rows)
    if not out_df.empty:
        out_df['Team'] = out_df['TeamHref'].apply(extract_team_from_href)
        out_df['Date'] = pd.to_datetime(out_df['Date'], errors='coerce')
        out_df['Date'] = out_df['Date'].dt.strftime('%m/%d/%Y')
        out_df['Opponent'] = out_df['Opponent'].apply(lambda o: normalize_opponent_text(o, DEFAULT_TEAM_REFS))
        final_df = out_df[['Team', 'Date', 'Opponent']].copy()
    else:
        final_df = pd.DataFrame(columns=['Team', 'Date', 'Opponent'])

    final_df.to_excel(output_xlsx, index=False)
    if verbose:
        print(f'Wrote {output_xlsx} with {len(final_df)} rows')
def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--year', type=int, default=2026)
    p.add_argument('--output', type=str, default=None)
    p.add_argument('--verbose', action='store_true', help='Print summary at end')
    p.add_argument('--limit', type=int, default=None, help='Limit number of teams to process (useful for testing)')
    p.add_argument('--save-initial', type=str, default=None, help='Optionally save the initial df to an xlsx file')
    return p.parse_args()

def main():
    args = parse_args()
    year = args.year
    output = args.output or f"{year}-Schedules-Extracted.xlsx"
    initial_df = build_initial_df(year)
    scrape_schedules(initial_df, year, output, verbose=args.verbose, limit=args.limit, save_initial=args.save_initial)

if __name__ == '__main__':
    main()


def run_schedule(year: int = 2026, output: str = None, verbose: bool = False, limit: int = None, save_initial: str = None):
    output = output or f"{year}-Schedules-Extracted.xlsx"
    initial_df = build_initial_df(year)
    scrape_schedules(initial_df, year, output, verbose=verbose, limit=limit, save_initial=save_initial)
    return output