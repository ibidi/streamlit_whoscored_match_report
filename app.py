import streamlit as st
import cloudscraper
import requests
from get_fotmob_headers import headers_leagues
from thefuzz import fuzz
from whoscored_match_report import whoscored_match_report
import io
import matplotlib.pyplot as plt
import base64
from datetime import datetime
from dateutil import parser
from playwright.sync_api import sync_playwright
import subprocess
import json
import re

# -----------------------
# Yardımcı Fonksiyonlar
# -----------------------

def install_playwright_browsers():
    try:
        subprocess.check_call(["playwright", "install", "firefox"])
    except Exception as e:
        st.write(f"[Playwright install error] {e}")

def fetch_matches_by_month_playwright(year_month: str):
    url = f"https://www.whoscored.com/tournaments/24627/data/?d={year_month}&isAggregate=false"

    try:
        install_playwright_browsers()

        with sync_playwright() as p:
            browser = p.firefox.launch(headless=True)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/111.0.0.0 Safari/537.36"
                )
            )
            page = context.new_page()
            page.goto(url, wait_until="networkidle")

            # JS render edilmiş content çek
            content = page.content()
            browser.close()

        # JSON'u script tag'inden çek
        # WhoScored data genelde window.__data=... formatında
        match = re.search(r"({.*})", content, re.DOTALL)
        if not match:
            return []

        data = json.loads(match.group(1))

        if not data.get("tournaments"):
            return []
        return data["tournaments"][0].get("matches", [])

    except Exception as e:
        st.write(f"[Playwright fetch error] {e}")
        return []


def get_all_played_matches():
    months = [
        "202508","202509","202510","202511","202512",
        "202601","202602","202603","202604","202605"
    ]

    all_matches = []
    stop = False

    for ym in months:
        matches = fetch_matches_by_month_playwright(ym)
        if not matches:
            continue

        for m in matches:
            # Eğer maç oynanmamışsa, döngüyü durdur (fonksiyonu hemen return etme)
            if m.get("homeScore") is None:
                stop = True
                break
            all_matches.append(m)

        if stop:
            break

    all_matches.sort(
        key=lambda x: parser.parse(x.get("startTimeUtc") or x.get("startTime")),
        reverse=True
    )
    return all_matches

def normalize_team_name(name):
    """WhoScored isimlerini Türkçe karakterli hale getirir ve küçük harfe çevirir"""
    name = name.lower()
    # İstanbul ve benzeri özel durumlar
    name = name.replace("istanbul basaksehir", "başakşehir")
    name = name.replace("fatih karagumruk", "fatih karagümrük")
    name = name.replace("genclerbirligi", "gençlerbirliği")
    name = name.replace("fenerbahce", "fenerbahçe")
    name = name.replace("besiktas", "beşiktaş")
    name = name.replace("goztepe", "göztepe")
    name = name.replace("kasimpasa", "kasımpaşa")
    name = name.replace("kayserispor", "kayserispor")
    name = name.replace("gaziantep fk", "gaziantep fk")
    name = name.replace("rizespor", "rizespor")
    name = name.replace("alanyaspor", "alanyaspor")
    name = name.replace("galatasaray", "galatasaray")
    name = name.replace("antalyaspor", "antalyaspor")
    name = name.replace("samsunspor", "samsunspor")
    name = name.replace("kocaelispor", "kocaelispor")
    return name.strip()

def find_fotmob_match(whoscored_match):
    """WhoScored maçına denk gelen FotMob maçını bul"""
    try:
        resp = requests.get(
            "https://www.fotmob.com/api/data/leagues?id=71&ccode3=TUR",
            headers=headers_leagues(71)
        )
        resp.raise_for_status()
        data = resp.json()
        all_matches = data.get("matches", {}).get("allMatches", [])

        # WhoScored zamanını UTC'ye çevir
        ws_time = whoscored_match["startTimeUtc"]
        ws_home = normalize_team_name(whoscored_match["homeTeamName"])
        ws_away = normalize_team_name(whoscored_match["awayTeamName"])

        for m in all_matches:
            fm_time = m["status"]["utcTime"]
            if fm_time != ws_time:
                continue

            fm_home = m["home"]["name"].lower()
            fm_away = m["away"]["name"].lower()

            home_score = fuzz.ratio(ws_home, fm_home)
            away_score = fuzz.ratio(ws_away, fm_away)

            if home_score >= 85 and away_score >= 85:
                return m["id"]

        return None
    except Exception as e:
        st.error(f"FotMob maç arama hatası: {e}")
        return None

# -----------------------
# Streamlit Arayüzü
# -----------------------

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"] {
    font-family: 'Poppins', sans-serif !important;
}
div[data-baseweb="select"] * {
    font-family: 'Poppins', sans-serif !important;
}
.sidebar .sidebar-content, .css-1d391kg {
    font-family: 'Poppins', sans-serif !important;
}
div[data-testid="stMarkdownContainer"] {
    font-family: 'Poppins', sans-serif !important;
}
li[role="option"] {
    font-family: 'Poppins', sans-serif !important;
}
</style>
""", unsafe_allow_html=True)


# Sidebar'a görsel ekleme
image_url = "https://images.fotmob.com/image_resources/logo/leaguelogo/71.png"  # Görselin URL'si

# Görseli bir HTML div ile ortalama
image_html = f"""<div style="display: flex; justify-content: center;">
        <img src="{image_url}" width="100">
    </div>
    """

st.sidebar.markdown(image_html, unsafe_allow_html=True)

st.set_page_config(page_title="Süper Lig - Maç Raporu", layout="wide")
st.sidebar.markdown(
    """

    <h2 style='text-align: center; 
               color:white; 
               font-family: "Poppins", sans-serif;'>
        Süper Lig - Maç Raporu
    </h2>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <style>
        /* Bilgisayarlar için */
        @media (min-width: 1024px) {
            .block-container {
                width: 1000px;
                max-width: 1000px;
            }
        }

        /* Tabletler için (genellikle 768px - 1024px arası ekran genişliği) */
        @media (min-width: 768px) and (max-width: 1023px) {
            .block-container.st-emotion-cache-13ln4jf.ea3mdgi5 {
                width: 700px;
                max-width: 700px;
            }
        }

        /* Telefonlar için (genellikle 768px ve altı ekran genişliği) */
        @media (max-width: 767px) {
            .block-container.st-emotion-cache-13ln4jf.ea3mdgi5 {
                width: 100%;
                max-width: 100%;
                padding-left: 10px;
                padding-right: 10px;
            }
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("""
<style>

div.stVerticalBlock {
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
}

/* Ortala */
div[data-testid="stDownloadButton"] {
    display: flex !important;
    justify-content: center !important;
    text-align: center !important;
    margin-top: 15px;
}

/* Butonun kendisini stillendir */
div[data-testid="stDownloadButton"] > button {
    background-color: rgba(51, 51, 51, 0.17) !important;
    color: gray !important;
    border: 0.5px solid gray !important;
    transition: background-color 0.5s ease !important;
    border-radius: 8px !important;
    padding: 8px 20px !important;
}

div[data-testid="stDownloadButton"] > button:hover {
    background-color: rgba(51, 51, 51, 0.65) !important;
    color: white !important;
}

div[data-testid="stDownloadButton"] > button:active {
    background-color: rgba(51, 51, 51, 0.3) !important;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def get_all_played_matches_cached():
    return get_all_played_matches()

@st.cache_data(show_spinner=False)
def generate_match_fig(whoscored_match_id, fotmob_match_id):
    return whoscored_match_report(whoscored_match_id, fotmob_match_id)

with st.sidebar:
    with st.spinner("📊 Maçlar yükleniyor..."):
        matches = get_all_played_matches_cached()

if matches:   
    if "selected_match" not in st.session_state:
        st.session_state.selected_match = matches[0]
        
    selected_match = st.sidebar.selectbox(
        "Maç Seç",
        options=matches,
        format_func=lambda m: f"{m['homeTeamName']} vs {m['awayTeamName']}"
    )
    st.session_state.selected_match = selected_match
    
    homeTeamName = selected_match['homeTeamName']
    awayTeamName = selected_match['awayTeamName']
    formatted_date = datetime.strptime(
        selected_match['startTimeUtc'], "%Y-%m-%dT%H:%M:%SZ"
    ).strftime("%d-%m-%Y")
    whoscored_match_id = selected_match['id']
    
    if whoscored_match_id:
        fotmob_match_id = find_fotmob_match(selected_match)
        if fotmob_match_id:
            # --- Fig ve buf session_state ile saklanacak ---
            if ("fig_buf" not in st.session_state) or (st.session_state.selected_match != selected_match):
                with st.spinner("📊 Maç raporu hazırlanıyor..."):
                    fig = generate_match_fig(whoscored_match_id, fotmob_match_id)
                    buf = io.BytesIO()
                    fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
                    buf.seek(0)
                    st.session_state.fig_buf = buf
                    plt.close(fig)
            else:
                buf = st.session_state.fig_buf
        
            # --- Base64 ile küçük önizleme ---
            img_data = base64.b64encode(buf.getvalue()).decode()
            html_code = f"""
            <div style="text-align:center;">
                <img src="data:image/png;base64,{img_data}" 
                     alt="Maç Raporu" 
                     style="width:65%; height:auto; border-radius:8px;" />
            </div>
            """
            st.markdown(html_code, unsafe_allow_html=True)
        
            # --- Dosya adı ve download butonu ---
            homeTeamName_replaced = str(homeTeamName).replace(' ', '_')
            awayTeamName_replaced = str(awayTeamName).replace(' ', '_')
            match_name_replaced = f"{homeTeamName_replaced}_{awayTeamName_replaced}"
            date_replaced = formatted_date.replace('.', '_')
            file_name = f"{match_name_replaced}_{date_replaced}_Mac_Raporu.png"
        
            st.download_button(
                label="Grafiği İndir",
                data=buf,
                file_name=file_name,
                mime="image/png"
            )
        
        else:
            st.warning("FotMob maç ID'si bulunamadı.")
else:
    st.warning("Henüz oynanmış maç bulunamadı.")
    
# Function to convert image to base64
def img_to_base64(img_path):
    with open(img_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Signature section
st.sidebar.markdown("---")  # Add a horizontal line to separate your signature from the content

# Load and encode icons
twitter_icon_base64 = img_to_base64("icons/twitter.png")
github_icon_base64 = img_to_base64("icons/github.png")
twitter_icon_white_base64 = img_to_base64("icons/twitter_white.png")  # White version of Twitter icon
github_icon_white_base64 = img_to_base64("icons/github_white.png")  # White version of GitHub icon

# Display the icons with links at the bottom of the sidebar
st.sidebar.markdown(
    f"""
    <style>
    .sidebar {{
        width: auto;
    }}
    .sidebar-content {{
        display: flex;
        flex-direction: column;
        height: 100%;
        margin-top: 10px;
    }}
    .icon-container {{
        display: flex;
        justify-content: center;
        margin-top: auto;
        padding-bottom: 20px;
        gap: 30px;  /* Space between icons */
    }}
    .icon-container img {{
        transition: filter 0.5s cubic-bezier(0.4, 0, 0.2, 1);  /* Smooth and natural easing */
    }}
    .icon-container a:hover img {{
        filter: brightness(0) invert(1);  /* Inverts color to white */
    }}
    </style>
    <div class="sidebar-content">
        <!-- Other sidebar content like selectbox goes here -->
        <div class="icon-container">
            <a href="https://x.com/bariscanyeksin" target="_blank">
                <img src="data:image/png;base64,{twitter_icon_base64}" alt="Twitter" width="30">
            </a>
            <a href="https://github.com/bariscanyeksin" target="_blank">
                <img src="data:image/png;base64,{github_icon_base64}" alt="GitHub" width="30">
            </a>
        </div>
    </div>
    """,
    unsafe_allow_html=True

)















