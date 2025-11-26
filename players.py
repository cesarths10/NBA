import os
import re
from typing import Optional
import pandas as pd
import requests
from bs4 import BeautifulSoup

URL = "https://basketball.realgm.com/nba/players"
DEFAULT_OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "players.xlsx")
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/91.0.4472.124 Safari/537.36"
)

def _parse_table_rows_from_soup(soup: BeautifulSoup) -> list[dict]:
    table = soup.find("table")
    if not table:
        return []
    tbody = table.find("tbody")
    if not tbody:
        return []

    rows = []
    for tr in tbody.find_all("tr"):
        def td_text(dt: str) -> str:
            td = tr.find("td", attrs={"data-th": dt})
            return td.get_text(strip=True) if td else ""

        player_cell = tr.find("td", attrs={"data-th": "Player"})
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
    return rows

def _scrape_with_requests(out_path: str) -> bool:
    headers = {"User-Agent": USER_AGENT}
    try:
        resp = requests.get(URL, headers=headers, timeout=15)
    except Exception:
        return False
    if resp.status_code != 200:
        return False

    soup = BeautifulSoup(resp.text, "lxml")
    rows = _parse_table_rows_from_soup(soup)
    if not rows:
        return False

    df = pd.DataFrame(rows, columns=["Player", "Pos", "Age", "Current Team", "YOS", "PlayerHref", "PlayerID"])
    try:
        if os.path.exists(out_path):
            try:
                os.remove(out_path)
            except Exception:
                pass
        df.to_excel(out_path, index=False)
        return True
    except Exception:
        return False

def run_players(out_path: Optional[str] = None) -> str:
    out_path = out_path or DEFAULT_OUTPUT
    ok = _scrape_with_requests(out_path)
    return out_path if ok else ""


if __name__ == "__main__":
    run_players()