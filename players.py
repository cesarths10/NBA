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

URL = "https://basketball.realgm.com/nba/players"
DEFAULT_OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "players.csv")


def _parse_table_rows_from_soup(soup: BeautifulSoup) -> list[dict]:
    tables = soup.find_all("table")
    if not tables:
        print("Error: No tables found in page source")
        return []

    for table in tables:
        rows = []
        for tr in table.find_all("tr"):
            def td_text(dt: str) -> str:
                td = tr.find("td", attrs={"data-th": dt})
                return td.get_text(strip=True) if td else ""

            player_cell = tr.find("td", attrs={"data-th": "Player"})
            if not player_cell:
                continue

            player_name = ""
            player_link = ""
            if player_cell:
                a = player_cell.find("a")
                if a:
                    player_name = a.get_text(strip=True)
                    player_link = a.get("href", "")
                else:
                    player_name = player_cell.get_text(strip=True)
            
            pid = ""
            if player_link:
                m = re.search(r"/Summary/(\d+)", player_link)
                if m:
                    pid = m.group(1)

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
        
        if rows:
            print(f"Found {len(rows)} players in table")
            return rows
            
    print("No valid player rows found in any table")
    return []

def _fetch_html_curl_cffi(url: str) -> str:
    try:
        from curl_cffi import requests
        print(f"Fetching {url} using curl_cffi (Chrome impersonation)...")
        resp = requests.get(url, impersonate="chrome120", timeout=30)
        if resp.status_code == 200:
            return resp.text
        print(f"curl_cffi returned status code: {resp.status_code}")
    except Exception as e:
        print(f"curl_cffi fetch failed: {e}")
    return ""


def _scrape_with_selenium(url: str = URL) -> str:
    try:
        print("Setting up Selenium as fallback...")
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        try:
            print(f"Fetching {url} with Selenium...")
            driver.get(url)
            time.sleep(10)
            html = driver.page_source
            print(f"Page Title: {driver.title}")
            return html
        finally:
            driver.quit()
    except Exception:
        print("Exception during Selenium scrape")
        traceback.print_exc()
        return ""


def _save_players_to_csv(html: str, out_path: str) -> bool:
    if not html:
        return False
    soup = BeautifulSoup(html, "lxml")
    rows = _parse_table_rows_from_soup(soup)
    
    if not rows:
        print("No rows found to save")
        return False

    df = pd.DataFrame(rows, columns=["Player", "Pos", "Age", "Current Team", "YOS", "PlayerHref", "PlayerID"])
    try:
        if os.path.exists(out_path):
            try:
                os.remove(out_path)
                print(f"Removed existing {out_path}")
            except Exception:
                print(f"Failed to remove {out_path}")
                traceback.print_exc()
        df.to_csv(out_path, index=False, encoding="utf-8")
        print(f"Successfully wrote {len(df)} players to {out_path}")
        return True
    except Exception:
        print("Exception during csv write")
        traceback.print_exc()
        return False


def run_players(out_path: Optional[str] = None) -> str:
    out_path = out_path or DEFAULT_OUTPUT
    # 1. Try curl_cffi with Chrome TLS impersonation (fast & bypasses Cloudflare)
    html = _fetch_html_curl_cffi(URL)
    if html and "<table" in html:
        ok = _save_players_to_csv(html, out_path)
        if ok:
            return out_path
            
    # 2. Fallback to Selenium
    print("Falling back to Selenium...")
    html = _scrape_with_selenium(URL)
    ok = _save_players_to_csv(html, out_path)
    return out_path if ok else ""


if __name__ == "__main__":
    run_players()
