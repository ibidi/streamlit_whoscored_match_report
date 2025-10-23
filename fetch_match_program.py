import requests
import json
import re
import csv
from thefuzz import fuzz
from dateutil import parser
from seleniumbase import Driver
from get_fotmob_headers import headers_leagues

# -----------------------
# Yardımcı Fonksiyonlar
# -----------------------

def normalize_team_name(name):
    """Takım isimlerini küçük harfe çevir ve Türkçe karakterleri düzelt"""
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

def fetch_whoscored_matches_by_month(year_month: str):
    """WhoScored maçlarını SeleniumBase ile çek (debug: içerik print ediliyor)"""
    url = f"https://www.whoscored.com/tournaments/24627/data/?d={year_month}&isAggregate=false"

    try:
        # UC moduyla (Undetected ChromeDriver) ve headless çalıştır
        driver = Driver(uc=True, headless=True)
        driver.get(url)

        # Sayfa içeriğini al
        content = driver.page_source

        # Debug: sayfa içeriğinin ilk 1000 karakteri
        print(f"[WhoScored debug] Page content snippet ({year_month}):")
        print(content[:1000])

        # Browser kapat
        driver.quit()

        # JSON extraction
        match = re.search(r"({.*})", content, re.DOTALL)
        if not match:
            print(f"[WhoScored fetch error] JSON not found for {year_month}")
            return []

        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError as je:
            print(f"[WhoScored fetch error] JSON decode error: {je}")
            # debug için içerik snippet
            print(f"Content snippet for JSON decode: {content[:500]} ...")
            return []

        if not data.get("tournaments"):
            print(f"[WhoScored fetch error] No tournaments key for {year_month}")
            return []

        return data["tournaments"][0].get("matches", [])

    except Exception as e:
        print(f"[SeleniumBase fetch error] {e}")
        try:
            driver.quit()
        except:
            pass
        return []

def get_all_whoscored_matches():
    months = ["202508","202509","202510","202511","202512",
              "202601","202602","202603","202604","202605"]
    all_matches = []

    for ym in months:
        matches = fetch_whoscored_matches_by_month(ym)
        for m in matches:
            if m.get("homeScore") is not None:
                all_matches.append(m)

    return all_matches

def fetch_fotmob_matches():
    """FotMob maçlarını al"""
    try:
        resp = requests.get(
            "https://www.fotmob.com/api/data/leagues?id=71&ccode3=TUR",
            headers=headers_leagues(71)
        )
        resp.raise_for_status()
        data = resp.json()
        all_matches = data.get("matches", {}).get("allMatches", [])
        
        # Sadece oynanmış maçlar
        played_matches = [m for m in all_matches if m.get("status", {}).get("finished") == True]
        return played_matches
    except Exception as e:
        print(f"[FotMob fetch error] {e}")
        return []

def find_whoscored_match_for_fotmob(fm, whoscored_matches):
    """FotMob maçına denk gelen WhoScored maçını bul"""
    fm_home = normalize_team_name(fm["home"]["name"])
    fm_away = normalize_team_name(fm["away"]["name"])
    fm_time = fm["status"]["utcTime"]

    for ws in whoscored_matches:
        ws_time = ws["startTimeUtc"]
        ws_home = normalize_team_name(ws["homeTeamName"])
        ws_away = normalize_team_name(ws["awayTeamName"])

        if fm_time != ws_time:
            continue

        home_score = fuzz.ratio(fm_home, ws_home)
        away_score = fuzz.ratio(fm_away, ws_away)

        if home_score >= 85 and away_score >= 85:
            return ws["id"]
    return None

# -----------------------
# Ana İşlem
# -----------------------

def main():
    print("FotMob maçları çekiliyor...")
    fotmob_matches = fetch_fotmob_matches()
    print(f"{len(fotmob_matches)} FotMob maçı bulundu.")

    print("WhoScored maçları çekiliyor...")
    whoscored_matches = get_all_whoscored_matches()
    print(f"{len(whoscored_matches)} WhoScored maçı bulundu.")

    result_rows = []
    for fm in fotmob_matches:
        ws_id = find_whoscored_match_for_fotmob(fm, whoscored_matches)
        week = fm["round"]
        home_name = fm["home"]["name"]
        away_name = fm["away"]["name"]
        match_name = f"{home_name} - {away_name}"
        result_rows.append({
            "week": week,
            "homeName": home_name,
            "awayName": away_name,
            "matchName": match_name,
            "fotmobId": fm["id"],
            "whoscoredId": ws_id
        })

    result_rows.reverse()
    
    csv_file = "super_lig_match_program.csv"
    with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["week", "homeName","awayName","matchName","fotmobId","whoscoredId"])
        writer.writeheader()
        for row in result_rows:
            writer.writerow(row)

    print(f"CSV oluşturuldu: {csv_file}")

if __name__ == "__main__":
    main()
