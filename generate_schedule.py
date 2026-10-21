# Import standard libraries for CLI parsing, timing, regex, and type hinting
import argparse
import pandas as pd
import time
import requests
from bs4 import BeautifulSoup
import re
from typing import Optional, List
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Standard browser User-Agent header to avoid scraper blocking
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"

# Master list of all 30 NBA team URL slug references on RealGM
DEFAULT_TEAM_REFS = [
    'Atlanta-Hawks','Boston-Celtics','Brooklyn-Nets','Charlotte-Hornets','Chicago-Bulls',
    'Cleveland-Cavaliers','Dallas-Mavericks','Denver-Nuggets','Detroit-Pistons','Golden-State-Warriors',
    'Houston-Rockets','Indiana-Pacers','Los-Angeles-Clippers','Los-Angeles-Lakers','Memphis-Grizzlies',
    'Miami-Heat','Milwaukee-Bucks','Minnesota-Timberwolves','New-Orleans-Pelicans','New-York-Knicks',
    'Oklahoma-City-Thunder','Orlando-Magic','Philadelphia-Sixers','Phoenix-Suns','Portland-Trail-Blazers',
    'Sacramento-Kings','San-Antonio-Spurs','Toronto-Raptors','Utah-Jazz','Washington-Wizards'
]

# Build initial DataFrame mapping each NBA team to its RealGM schedule URL for the specified year
def build_initial_df(year: int, team_refs: list = None) -> pd.DataFrame:
    # Use default 30 NBA teams if no custom team list is provided
    team_refs = team_refs or DEFAULT_TEAM_REFS
    # Template URL for team season schedules on RealGM
    base = 'https://basketball.realgm.com/nba/teams/{team_ref}/1/Schedule/{year}'
    # Construct row dictionaries for each team reference and target year
    rows = [{'TeamRef': tr, 'Schedule': base.format(team_ref=tr, year=year)} for tr in team_refs]
    # Return structured DataFrame containing team names and schedule URLs
    return pd.DataFrame(rows)

# Extract clean opponent team name from the schedule table cell
def extract_opponent_text(td):
    # Check if opponent is wrapped in an anchor link tag
    a = td.find('a')
    # If anchor tag contains text, return stripped team name
    if a and a.text:
        return a.text.strip()
    # Fall back to stripping text with spaces from the table cell
    txt = td.get_text(separator=' ', strip=True)
    # Strip home/away prefixes like 'v.' or '@' from opponent string
    for marker in ['v.', '@']:
        # If text starts with match marker, remove prefix
        if txt.startswith(marker):
            return txt[len(marker):].strip()
    # Return raw stripped cell text if no prefix matched
    return txt

# Extract clean team slug from RealGM team hyperlink
def extract_team_from_href(href: str) -> str:
    # Ensure href is a valid string before regex extraction
    if not isinstance(href, str):
        return ''
    # Match team slug pattern between /teams/ and the trailing slash
    m = re.search(r"/teams/([^/]+)/", href)
    # Return captured team slug if pattern matched
    if m:
        return m.group(1)
    # Return original href string as fallback
    return href

# Normalize opponent text against known team references using fuzzy match scoring
def normalize_opponent_text(opp: str, team_refs: list) -> str:
    # Return empty string if opponent text is invalid or null
    if not isinstance(opp, str):
        return ''
    # Collapse multiple whitespace characters into a single space
    s_norm = re.sub(r"\s+", " ", opp.strip()).strip()
    s_lower = s_norm.lower()
    best = None
    best_score = 0
    # Iterate through all known team references to find best match
    for tr in team_refs:
        # Convert hyphenated slug to lowercase spaced words
        tr_norm = tr.replace('-', ' ').lower()
        # Return exact match immediately if lowercase strings are equal
        if s_lower == tr_norm:
            return tr
        # Check substring match when input is contained within team name
        if s_lower in tr_norm:
            score = len(s_lower)
            # Update best candidate if length score exceeds current best
            if score > best_score:
                best = tr
                best_score = score
        # Check reverse substring match when team name is within input
        elif tr_norm in s_lower:
            score = len(tr_norm)
            # Update best candidate if length score exceeds current best
            if score > best_score:
                best = tr
                best_score = score
    # Return closest matching team reference if found
    if best:
        return best
    # Fall back to title-cased hyphen-separated string
    return '-'.join([w.capitalize() for w in s_norm.split()])

# Fetch page HTML with session timeout handling and HTTP error status checks
def fetch_html_requests(session: requests.Session, url: str, timeout: int = 15) -> str:
    # Execute HTTP GET request with configured session and timeout
    try:
        r = session.get(url, timeout=timeout)
        # Raise HTTPError if status code is 4xx or 5xx
        r.raise_for_status()
        # Return raw response HTML string
        return r.text
    # Catch connection errors, timeouts, or invalid HTTP responses safely
    except Exception:
        return ''

# Scrape game schedules for all teams in the season DataFrame and output to Excel
def scrape_schedules(season_df: pd.DataFrame, year: int, output_xlsx: str, *,
                     verbose: bool = False,
                     limit: Optional[int] = None, save_initial: Optional[str] = None):
    # Initialize persistent requests session for connection pooling
    session = requests.Session()
    session.headers.update({'User-Agent': USER_AGENT})
    # Configure retry logic with exponential backoff for rate limits and server errors
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["HEAD", "GET", "OPTIONS"])
    adapter = HTTPAdapter(max_retries=retries)
    # Mount retry adapter across both HTTPS and HTTP protocols
    session.mount('https://', adapter)
    session.mount('http://', adapter)

    # Standardize column naming if TeamRef was passed instead of TeamHref
    if 'TeamHref' not in season_df.columns and 'TeamRef' in season_df.columns:
        season_df = season_df.rename(columns={'TeamRef': 'TeamHref'})

    # Optionally persist the initial team schedule URL list to an Excel file
    if save_initial:
        season_df.to_excel(save_initial, index=False)

    rows = []
    # Collect unique team reference slugs from the input DataFrame
    team_refs = list(season_df['TeamHref'].dropna().unique()) if 'TeamHref' in season_df.columns else []
    # Slice rows if a testing limit was specified
    if limit:
        iterable = list(season_df.iterrows())[:limit]
    # Otherwise process all team rows in the DataFrame
    else:
        iterable = season_df.iterrows()

    # Iterate through each team schedule URL to scrape game matchups
    for idx, row in iterable:
        team_href = row.get('TeamHref')
        schedule_url = row.get('Schedule')
        # Skip row if schedule URL is missing or empty
        if pd.isna(schedule_url) or not schedule_url:
            continue
        # Prepend base domain if schedule URL is a relative path
        if schedule_url.startswith('/'):
            schedule_url = 'https://basketball.realgm.com' + schedule_url

        html = ''
        # Request schedule webpage HTML via requests session
        html = fetch_html_requests(session, schedule_url)

        # Pause and continue if request failed or returned empty HTML
        if not html:
            time.sleep(1)
            continue

        # Parse schedule HTML using BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        # Locate the schedule data table by data-toggle attribute or CSS class
        table = soup.find('table', attrs={'data-toggle': 'table'}) or soup.find('table', class_='table')
        # Skip if no schedule table was found on page
        if not table:
            time.sleep(1)
            continue
        # Locate the tbody element containing individual game rows
        tbody = table.find('tbody')
        # Skip if table has no tbody element
        if not tbody:
            time.sleep(1)
            continue

        # Iterate through every game row in the schedule table
        for tr in tbody.find_all('tr'):
            tds = tr.find_all('td')
            # Ensure row contains at least date and opponent cells
            if len(tds) < 2:
                continue
            date_td = tds[0]
            opp_td = tds[1]
            date_text = date_td.get_text(separator=' ', strip=True)
            a_date = date_td.find('a')
            # Extract date text from inner anchor tag if present
            if a_date and a_date.text:
                date_text = a_date.text.strip()
            # Extract clean opponent team name from cell
            opp_text = extract_opponent_text(opp_td)
            # Append structured game record dictionary
            rows.append({'TeamHref': team_href, 'ScheduleURL': schedule_url, 'Date': date_text, 'Opponent': opp_text})

        # Polite rate-limiting sleep between team schedule requests
        time.sleep(0.8)

    # Convert collected game rows into a DataFrame
    out_df = pd.DataFrame(rows)
    # Format dates and normalize team names if records were found
    if not out_df.empty:
        # Extract clean team identifier from URL slug
        out_df['Team'] = out_df['TeamHref'].apply(extract_team_from_href)
        # Standardize date format to MM/DD/YYYY
        out_df['Date'] = pd.to_datetime(out_df['Date'], errors='coerce')
        out_df['Date'] = out_df['Date'].dt.strftime('%m/%d/%Y')
        # Normalize opponent name against known NBA team slugs
        out_df['Opponent'] = out_df['Opponent'].apply(lambda o: normalize_opponent_text(o, DEFAULT_TEAM_REFS))
        # Keep only essential schedule columns
        final_df = out_df[['Team', 'Date', 'Opponent']].copy()
    # Create empty DataFrame schema if no rows were scraped
    else:
        final_df = pd.DataFrame(columns=['Team', 'Date', 'Opponent'])

    # Write final schedule DataFrame to Excel output file
    final_df.to_excel(output_xlsx, index=False)
    # Print status summary if verbose output flag is active
    if verbose:
        print(f'Wrote {output_xlsx} with {len(final_df)} rows')

# Parse CLI arguments for schedule year, output filename, and rate limits
def parse_args():
    p = argparse.ArgumentParser()
    # Target NBA season year (e.g. 2026 for 2025-26 season)
    p.add_argument('--year', type=int, default=2026)
    # Custom output Excel filepath
    p.add_argument('--output', type=str, default=None)
    # Verbose logging flag
    p.add_argument('--verbose', action='store_true', help='Print summary at end')
    # Limit number of teams to scrape for testing
    p.add_argument('--limit', type=int, default=None, help='Limit number of teams to process (useful for testing)')
    # Save unparsed initial team URLs to Excel
    p.add_argument('--save-initial', type=str, default=None, help='Optionally save the initial df to an xlsx file')
    return p.parse_args()

# CLI entrypoint to parse arguments and execute the schedule scraper
def main():
    args = parse_args()
    year = args.year
    output = args.output or f"{year}-Schedules-Extracted.xlsx"
    # Construct team schedule URL mapping
    initial_df = build_initial_df(year)
    # Execute scraping workflow
    scrape_schedules(initial_df, year, output, verbose=args.verbose, limit=args.limit, save_initial=args.save_initial)

# Run CLI entrypoint when executed directly
if __name__ == '__main__':
    main()

# Programmatic entrypoint to run schedule extraction from external scripts
def run_schedule(year: int = 2026, output: str = None, verbose: bool = False, limit: int = None, save_initial: str = None):
    # Set default Excel output file name based on target year
    output = output or f"{year}-Schedules-Extracted.xlsx"
    # Construct initial team schedule URLs
    initial_df = build_initial_df(year)
    # Scrape all schedules and write output file
    scrape_schedules(initial_df, year, output, verbose=verbose, limit=limit, save_initial=save_initial)
    return output