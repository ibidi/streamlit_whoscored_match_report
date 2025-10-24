import requests
import json
import re
import csv
from thefuzz import fuzz
from dateutil import parser
from playwright.sync_api import sync_playwright
from get_fotmob_headers import headers_leagues

# -----------------------
# Yardımcı Fonksiyonlar
# -----------------------

def normalize_team_name(name):
    name = name.lower()
    name = name.replace("istanbul basaksehir", "başakşehir")
    name = name.replace("fatih karagumruk", "fatih karagümrük")
    name = name.replace("genclerbirligi", "gençlerbirliği")
    name = name.replace("fenerbahce", "fenerbahçe")
    name = name.replace("besiktas", "beşiktaş")
    name = name.replace("goztepe", "göztepe")
    name = name.replace("kasimpasa", "kasımpaşa")
    name = name.replace("galatasaray", "galatasaray")
    name = name.replace("antalyaspor", "antalyaspor")
    name = name.replace("samsunspor", "samsunspor")
    name = name.replace("kocaelispor", "kocaelispor")
    return name.strip()

# -----------------------
# Cloudflare-safe WhoScored Fetcher (Refactored)
# -----------------------

def get_whoscored_matches_by_months():
    # Çekilecek aylar
    months = [
        "202508","202509","202510","202511","202512",
        "202601","202602","202603","202604","202605"
    ]
    
    # Ana fixtures sayfası
    page_url = "https://www.whoscored.com/tournaments/24627/fixtures/turkey-super-lig-2025-2026"

    collected = []

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1440, "height": 900},
            locale="tr-TR"
        )

        page = context.new_page()

        # JSON intercept handler
        def handle_response(response):
            url = response.url
            if "/tournaments/24627/data/?d=" in url:
                try:
                    data = response.json()
                    matches = data["tournaments"][0]["matches"]
                    for m in matches:
                        if m.get("homeScore") is not None:
                            collected.append(m)
                except:
                    pass

        page.on("response", handle_response)

        # Sayfa açılır, Cloudflare cookie verilir
        page.goto(page_url, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(4000)

        # JSON endpoint'lerini tetikle
        for ym in months:
            api_url = f"https://www.whoscored.com/tournaments/24627/data/?d={ym}&isAggregate=false"
            page.evaluate(f"fetch('{api_url}')")
            page.wait_for_timeout(1500)

        browser.close()

    return collected

# -----------------------
# FotMob Fetch
# -----------------------

def fetch_fotmob_matches():
    try:
        resp = requests.get(
            "https://www.fotmob.com/api/data/leagues?id=71&ccode3=TUR",
            headers=headers_leagues(71)
        )
        resp.raise_for_status()
        data = resp.json()
        all_matches = data.get("matches", {}).get("allMatches", [])
        return [m for m in all_matches if m.get("status", {}).get("finished") == True]
    except Exception as e:
        print(f"[FotMob fetch error] {e}")
        return []

# -----------------------
# Matcher
# -----------------------

def find_whoscored_match_for_fotmob(fm, whoscored_matches):
    fm_home = normalize_team_name(fm["home"]["name"])
    fm_away = normalize_team_name(fm["away"]["name"])
    fm_time = fm["status"]["utcTime"]

    for ws in whoscored_matches:
        if ws["startTimeUtc"] != fm_time:
            continue

        ws_home = normalize_team_name(ws["homeTeamName"])
        ws_away = normalize_team_name(ws["awayTeamName"])

        if fuzz.ratio(fm_home, ws_home) >= 85 and fuzz.ratio(fm_away, ws_away) >= 85:
            return ws["id"]

    return None

# -----------------------
# Ana İşlem
# -----------------------

def main():
    print("FotMob maçları çekiliyor...")
    fotmob = fetch_fotmob_matches()
    print(f"{len(fotmob)} FotMob maçı bulundu.")

    print("WhoScored maçları Cloudflare güvenli modda çekiliyor...")
    whoscored = get_whoscored_matches_by_months()
    print(f"{len(whoscored)} WhoScored maçı bulundu.")

    rows = []
    for fm in fotmob:
        ws_id = find_whoscored_match_for_fotmob(fm, whoscored)
        rows.append({
            "week": fm["round"],
            "homeName": fm["home"]["name"],
            "awayName": fm["away"]["name"],
            "matchName": f"{fm['home']['name']} - {fm['away']['name']}",
            "fotmobId": fm["id"],
            "whoscoredId": ws_id
        })

    rows.reverse()

    with open("super_lig_match_program.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["week", "homeName","awayName","matchName","fotmobId","whoscoredId"])
        writer.writeheader()
        writer.writerows(rows)

    print("[OK] CSV oluşturuldu: super_lig_match_program.csv")

if __name__ == "__main__":
    main()
