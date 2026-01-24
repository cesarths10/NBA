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
DEFAULT_OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "players.xlsx")


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

def _scrape_with_selenium(out_path: str) -> bool:
    try:
        print(f"Setting up Selenium...")
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument(f"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        # Bypass detection by removing 'webdriver' property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        try:
            print(f"Fetching {URL}...")
            driver.get(URL)
            time.sleep(10) # Wait for page and cloudflare challenge if any
            html = driver.page_source
            print(f"Page Title: {driver.title}")
        finally:
            driver.quit()
        
        print("Page retrieved")
    except Exception:
        print("Exception during Selenium scrape")
        traceback.print_exc()
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
        df.to_excel(out_path, index=False)
        print(f"Successfully wrote to {out_path}")
        return True
    except Exception:
        print("Exception during excel write")
        traceback.print_exc()
        return False

def run_players(out_path: Optional[str] = None) -> str:
    out_path = out_path or DEFAULT_OUTPUT
    ok = _scrape_with_selenium(out_path)
    return out_path if ok else ""


if __name__ == "__main__":
    run_players()