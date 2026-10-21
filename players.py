# Import standard libraries for filesystem, regex, typing, web scraping, and browser automation
import os
import re
from typing import Optional
import pandas as pd
from bs4 import BeautifulSoup
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# Target RealGM URL for active NBA player rosters
URL = "https://basketball.realgm.com/nba/players"
# Default output CSV path in the project directory
DEFAULT_OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "players.csv")

# Parse HTML tables to extract structured player rows (name, position, age, team, YOS, player ID)
def _parse_table_rows_from_soup(soup: BeautifulSoup) -> list[dict]:
    # Find all table elements in the parsed HTML document
    tables = soup.find_all("table")
    # Return empty list if no tables are found on page
    if not tables:
        print("Error: No tables found in page source")
        return []

    # Iterate through all tables on page to locate player data
    for table in tables:
        rows = []
        # Iterate through every table row element
        for tr in table.find_all("tr"):
            # Helper function to extract stripped text from cell with data-th attribute
            def td_text(dt: str) -> str:
                td = tr.find("td", attrs={"data-th": dt})
                return td.get_text(strip=True) if td else ""

            # Locate the Player cell to verify this is a valid roster row
            player_cell = tr.find("td", attrs={"data-th": "Player"})
            # Skip non-player rows such as subheaders or footers
            if not player_cell:
                continue

            player_name = ""
            player_link = ""
            # Extract player display name and profile URL from anchor tag
            if player_cell:
                a = player_cell.find("a")
                # Extract text and relative href if link tag is present
                if a:
                    player_name = a.get_text(strip=True)
                    player_link = a.get("href", "")
                # Fall back to raw text if no link tag exists
                else:
                    player_name = player_cell.get_text(strip=True)
            
            pid = ""
            # Extract numeric RealGM player ID from summary URL
            if player_link:
                m = re.search(r"/Summary/(\d+)", player_link)
                # Capture player ID digit string
                if m:
                    pid = m.group(1)

            # Append clean player metadata dictionary
            rows.append(
                {
                    "Player": player_name,
                    "PlayerHref": player_link or "",
                    "Pos": td_text("Pos"),
                    "Age": td_text("Age"),
                    "Current Team": td_text("Current Team"),
                    "YOS": td_text("YOS"),
                    "PlayerID": pid,
                }
            )
        
        # If valid rows were parsed from this table, return them immediately
        if rows:
            print(f"Found {len(rows)} players in table")
            return rows
            
    # Log warning if no matching player rows were identified in any table
    print("No valid player rows found in any table")
    return []

# Fetch webpage HTML using curl_cffi with Chrome TLS impersonation to bypass Cloudflare
def _fetch_html_curl_cffi(url: str) -> str:
    # Safely attempt curl_cffi request with Chrome 120 browser fingerprinting
    try:
        from curl_cffi import requests
        print(f"Fetching {url} using curl_cffi (Chrome impersonation)...")
        # Impersonate modern desktop Chrome browser with 30-second timeout
        resp = requests.get(url, impersonate="chrome120", timeout=30)
        # Return response text if HTTP status code is 200 OK
        if resp.status_code == 200:
            return resp.text
        # Log non-200 HTTP status code
        print(f"curl_cffi returned status code: {resp.status_code}")
    # Catch curl_cffi exceptions or connection timeouts
    except Exception as e:
        print(f"curl_cffi fetch failed: {e}")
    # Return empty string if curl_cffi request failed
    return ""

# Fallback headless Chrome scraper using Selenium when curl_cffi is blocked or unavailable
def _scrape_with_selenium(url: str = URL) -> str:
    # Setup and execute headless Chrome driver
    try:
        print("Setting up Selenium as fallback...")
        options = Options()
        # Run headless with modern Chrome headless engine
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        # Mask automation flags to prevent bot detection
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Initialize Chrome driver with automated webdriver manager
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        # Safely fetch page and guarantee browser shutdown in finally block
        try:
            print(f"Fetching {url} with Selenium...")
            driver.get(url)
            # Allow JavaScript to render dynamic player roster table
            time.sleep(10)
            html = driver.page_source
            print(f"Page Title: {driver.title}")
            return html
        # Ensure browser process is always terminated cleanly
        finally:
            driver.quit()
    # Catch any driver startup, network, or timeout exceptions
    except Exception:
        print("Exception during Selenium scrape")
        traceback.print_exc()
        return ""

# Parse HTML, convert extracted player rows into a pandas DataFrame, and write to CSV
def _save_players_to_csv(html: str, out_path: str) -> bool:
    # Return false immediately if HTML content is empty
    if not html:
        return False
    # Parse HTML using fast lxml parser
    soup = BeautifulSoup(html, "lxml")
    rows = _parse_table_rows_from_soup(soup)
    
    # Return false if no player rows were parsed
    if not rows:
        print("No rows found to save")
        return False

    # Build DataFrame with standardized roster schema columns
    df = pd.DataFrame(rows, columns=["Player", "Pos", "Age", "Current Team", "YOS", "PlayerHref", "PlayerID"])
    # Write DataFrame to output CSV with UTF-8 encoding
    try:
        # Remove pre-existing output file if present to guarantee fresh write
        if os.path.exists(out_path):
            try:
                os.remove(out_path)
                print(f"Removed existing {out_path}")
            # Catch file lock or permission errors during deletion
            except Exception:
                print(f"Failed to remove {out_path}")
                traceback.print_exc()
        # Export DataFrame to CSV without row index
        df.to_csv(out_path, index=False, encoding="utf-8")
        print(f"Successfully wrote {len(df)} players to {out_path}")
        return True
    # Catch CSV write or disk I/O errors
    except Exception:
        print("Exception during csv write")
        traceback.print_exc()
        return False

# Main player scraper orchestrator trying fast curl_cffi first with Selenium fallback
def run_players(out_path: Optional[str] = None) -> str:
    # Default to players.csv in script directory if no path specified
    out_path = out_path or DEFAULT_OUTPUT
    # Primary attempt: Try curl_cffi with Chrome TLS impersonation (fast & bypasses Cloudflare)
    html = _fetch_html_curl_cffi(URL)
    # Check if response returned valid table content
    if html and "<table" in html:
        ok = _save_players_to_csv(html, out_path)
        # Return path if curl_cffi scrape and CSV write succeeded
        if ok:
            return out_path
            
    # Secondary attempt: Fall back to headless Selenium browser
    print("Falling back to Selenium...")
    html = _scrape_with_selenium(URL)
    ok = _save_players_to_csv(html, out_path)
    # Return output path if scrape succeeded, or empty string on failure
    return out_path if ok else ""

# Execute player scraper when invoked directly from command line
if __name__ == "__main__":
    run_players()
