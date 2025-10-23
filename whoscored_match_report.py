import json
import re
import pandas as pd
import cloudscraper
from mplsoccer import Pitch, add_image
import matplotlib.pyplot as plt
import numpy as np
import os
from matplotlib import font_manager as fm
from PIL import Image
from io import BytesIO
import requests
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from datetime import datetime
from highlight_text import ax_text
from matplotlib.colors import to_rgba, LinearSegmentedColormap
from matplotlib.patches import FancyArrowPatch, Rectangle, FancyBboxPatch
import matplotlib.patheffects as path_effects
from unidecode import unidecode
import matplotlib.image as mpimg
from matplotlib.path import Path
import base64
import hashlib
from bs4 import BeautifulSoup

current_dir = os.path.dirname(os.path.abspath(__file__))

# Poppins fontunu yükleme
font_path = os.path.join(current_dir, 'fonts', 'Poppins-Regular.ttf')
prop = fm.FontProperties(fname=font_path)

bold_font_path = os.path.join(current_dir, 'fonts', 'Poppins-SemiBold.ttf')
bold_prop = fm.FontProperties(fname=bold_font_path)

def whoscored_match_report(whoscored_match_id, fotmob_match_id, fotmob_league_id=71):
    def get_version_number():
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'priority': 'u=0, i',
            'referer': 'https://www.google.com/',
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        }
        
        response = requests.get("https://www.fotmob.com/", headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        version_element = soup.find('span', class_=lambda cls: cls and 'VersionNumber' in cls)
        if version_element:
            return version_element.text.strip()
        else:
            return None
        
    version_number = get_version_number()

    def get_xmas_pass():
        url = 'https://raw.githubusercontent.com/bariscanyeksin/streamlit_radar/refs/heads/main/xmas_pass.txt'
        response = requests.get(url)
        if response.status_code == 200:
            file_content = response.text
            return file_content
        else:
            print(f"Failed to fetch the file: {response.status_code}")
            return None
        
    xmas_pass = get_xmas_pass()

    def create_xmas_header(url, password):
            try:
                timestamp = int(datetime.now().timestamp() * 1000)
                request_data = {
                    "url": url,
                    "code": timestamp,
                    "foo": version_number
                }
                
                json_string = f"{json.dumps(request_data, separators=(',', ':'))}{password.strip()}"
                signature = hashlib.md5(json_string.encode('utf-8')).hexdigest().upper()
                body = {
                    "body": request_data,
                    "signature": signature
                }
                encoded = base64.b64encode(json.dumps(body, separators=(',', ':')).encode('utf-8')).decode('utf-8')
                return encoded
            except Exception as e:
                return f"Error generating signature: {e}"

    def headers_matchDetails(match_id):
        api_url = "/api/matchDetails?matchId=" + str(match_id)
        xmas_value = create_xmas_header(api_url, xmas_pass)
        
        headers = {
            'accept': '*/*',
            'accept-language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'referer': f'https://www.fotmob.com/',
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'x-mas': f'{xmas_value}',
        }
        
        return headers

    def getFotmobData(fotmob_match_id):
        fotmob_match_url = f"https://www.fotmob.com/api/matchDetails?matchId={fotmob_match_id}"
        headers = {
            'sec-ch-ua-platform': '"Windows"',
            'Referer': 'https://www.fotmob.com/tr/leagues/71/overview/super-lig',
            'sec-ch-ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'sec-ch-ua-mobile': '?0',
            
        }
        fotmob_match_response = requests.get(fotmob_match_url, headers=headers_matchDetails(fotmob_match_id))
        fotmobData = fotmob_match_response.json()
        return fotmobData

    fotmobData = getFotmobData(fotmob_match_id)
    fotmobPlayerStats = fotmobData['content']['playerStats']
    shots_data = fotmobData['content']['shotmap']['shots']

    general_data = fotmobData['general']
    week = general_data['matchRound']
    matchDay = general_data['matchTimeUTCDate']
    parsed_date = datetime.fromisoformat(matchDay[:-1])
    formatted_date = parsed_date.strftime("%d.%m.%Y")
    leagueName = general_data['leagueName']
    #leagueSeason = general_data['parentLeagueSeason']
    leagueSeason = "2025/2026"
    leagueString = f"{leagueName} - {leagueSeason}"
    weekString = f"{week}. Hafta  |  {formatted_date}"
    homeTeamName = general_data['homeTeam']['name']
    homeTeamId = general_data['homeTeam']['id']
    homeColor = general_data['teamColors']['lightMode']['home']
    awayTeamName = general_data['awayTeam']['name']
    awayTeamId = general_data['awayTeam']['id']
    awayColor = general_data['teamColors']['lightMode']['away']
    result = fotmobData['header']['status']['scoreStr']
    result_string = f"{homeTeamName} {result} {awayTeamName}"
    matchDetailString = f"{leagueString}  |  {weekString}"

    def install_playwright_browsers():
        try:
            subprocess.check_call(["playwright", "install", "firefox"])
        except Exception as e:
            st.write(f"[Playwright install error] {e}")
    
    @st.cache_data(ttl=600)
    def fetch_whoscored_live_page(whoscored_match_id: int):
        url = f"https://www.whoscored.com/Matches/{whoscored_match_id}/Live"
        
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
    
                # HTML dump
                html = page.content()
    
                browser.close()
                return html
    
        except Exception as e:
            st.write(f"[Playwright fetch error] {e}")
            return None

    response_text = fetch_whoscored_live_page(whoscored_match_id)

    def extract_json_from_html(response_text):  
        # JSON formatını yakalamak için regex kalıbı
        regex_pattern = r'(?<=require\.config\.params\[\"args\"\].=.)[\s\S]*?;'
        match = re.search(regex_pattern, response_text, re.DOTALL)
        
        if not match:
            print("İlgili JSON verisi bulunamadı.")
            return None

        data_txt = re.findall(regex_pattern, response_text)[0]

        # add quotations for json parser
        data_txt = data_txt.replace('matchId', '"matchId"')
        data_txt = data_txt.replace('matchCentreData', '"matchCentreData"')
        data_txt = data_txt.replace('matchCentreEventTypeJson', '"matchCentreEventTypeJson"')
        data_txt = data_txt.replace('formationIdNameMappings', '"formationIdNameMappings"')
        data_txt = data_txt.replace('};', '}')

        return data_txt

    def extract_data_from_dict(data):
        # load data from json
        event_types = data["matchCentreEventTypeJson"]
        formation_mappings = data["formationIdNameMappings"]
        events_dict = data["matchCentreData"]["events"]
        teams_dict = {data["matchCentreData"]['home']['teamId']: data["matchCentreData"]['home']['name'],
                    data["matchCentreData"]['away']['teamId']: data["matchCentreData"]['away']['name']}
        players_dict = data["matchCentreData"]["playerIdNameDictionary"]
        # create players dataframe
        players_home_df = pd.DataFrame(data["matchCentreData"]['home']['players'])
        players_home_df["teamId"] = data["matchCentreData"]['home']['teamId']
        players_away_df = pd.DataFrame(data["matchCentreData"]['away']['players'])
        players_away_df["teamId"] = data["matchCentreData"]['away']['teamId']
        players_df = pd.concat([players_home_df, players_away_df])
        players_ids = data["matchCentreData"]["playerIdNameDictionary"]
        return event_types, events_dict, players_df, teams_dict, players_ids

    json_data_txt = extract_json_from_html(response_text)
    data = json.loads(json_data_txt)
    event_types, events_dict, players_df, teams_dict, players_ids = extract_data_from_dict(data)

    whoscored_team_map = {
        "Besiktas": "Beşiktaş",
        "Galatasaray": "Galatasaray",
        "Konyaspor": "Konyaspor",
        "Trabzonspor": "Trabzonspor",
        "Goztepe": "Göztepe",
        "Antalyaspor": "Antalyaspor",
        "Samsunspor": "Samsunspor",
        "Rizespor": "Rizespor",
        "Fenerbahce": "Fenerbahçe",
        "Alanyaspor": "Alanyaspor",
        "Kocaelispor": "Kocaelispor",
        "Kasimpasa": "Kasımpaşa",
        "Genclerbirligi": "Gençlerbirliği",
        "Eyupspor": "Eyüpspor",
        "Fatih Karagumruk": "Fatih Karagümrük",
        "Gaziantep FK": "Gaziantep FK",
    }

    teams_dict = {k: whoscored_team_map.get(v, v) for k, v in teams_dict.items()}
    df = pd.DataFrame(events_dict)

    # Sütunları doğrudan 'displayName' anahtarından alınacak şekilde düzenle
    df['type'] = df['type'].apply(lambda x: x['displayName'] if isinstance(x, dict) else None)
    df['outcomeType'] = df['outcomeType'].apply(lambda x: x['displayName'] if isinstance(x, dict) else None)
    df['period'] = df['period'].apply(lambda x: x['displayName'] if isinstance(x, dict) else None)

    df['x'] = df['x']*1.05
    df['y'] = df['y']*0.68
    df['endX'] = df['endX']*1.05
    df['endY'] = df['endY']*0.68
    df['goalMouthY'] = df['goalMouthY']*0.68

    pd.set_option('future.no_silent_downcasting', True)

    # temprary use of typeId of period column
    df['period'] = df['period'].replace({'FirstHalf': 1, 'SecondHalf': 2, 'FirstPeriodOfExtraTime': 3, 'SecondPeriodOfExtraTime': 4, 
                                        'PenaltyShootout': 5, 'PostGame': 14, 'PreMatch': 16})

    # new column for cumulative minutes, This part is taken from the "jakeyk11.github.io" github repository and modified for my use
    def cumulative_match_mins(events_df):
        events_out = pd.DataFrame()
        # Add cumulative time to events data, resetting for each unique match
        match_events = events_df.copy()
        match_events['cumulative_mins'] = match_events['minute'] + (1/60) * match_events['second']
        # Add time increment to cumulative minutes based on period of game.
        for period in np.arange(1, match_events['period'].max() + 1, 1):
            if period > 1:
                t_delta = match_events[match_events['period'] == period - 1]['cumulative_mins'].max() - \
                                    match_events[match_events['period'] == period]['cumulative_mins'].min()
            elif period == 1 or period == 5:
                t_delta = 0
            else:
                t_delta = 0
            match_events.loc[match_events['period'] == period, 'cumulative_mins'] += t_delta
        # Rebuild events dataframe
        events_out = pd.concat([events_out, match_events])
        return events_out

    df = cumulative_match_mins(df)

    # Extracting the carry data and merge it with the main df, This part is also taken from the "jakeyk11.github.io" github repository and modified for my use
    def insert_ball_carries(events_df, min_carry_length=3, max_carry_length=60, min_carry_duration=1, max_carry_duration=10):
        events_out = pd.DataFrame()
        # Carry conditions (convert from metres to opta)
        min_carry_length = 7.0
        max_carry_length = 60.0
        min_carry_duration = 1.0
        max_carry_duration = 10.0
        # match_events = events_df[events_df['match_id'] == match_id].reset_index()
        match_events = events_df.reset_index()
        match_carries = pd.DataFrame()
        
        for idx, match_event in match_events.iterrows():

            if idx < len(match_events) - 1:
                prev_evt_team = match_event['teamId']
                next_evt_idx = idx + 1
                init_next_evt = match_events.loc[next_evt_idx]
                take_ons = 0
                incorrect_next_evt = True

                while incorrect_next_evt:

                    next_evt = match_events.loc[next_evt_idx]

                    if next_evt['type'] == 'TakeOn' and next_evt['outcomeType'] == 'Successful':
                        take_ons += 1
                        incorrect_next_evt = True

                    elif ((next_evt['type'] == 'TakeOn' and next_evt['outcomeType'] == 'Unsuccessful')
                        or (next_evt['teamId'] != prev_evt_team and next_evt['type'] == 'Challenge' and next_evt['outcomeType'] == 'Unsuccessful')
                        or (next_evt['type'] == 'Foul')):
                        incorrect_next_evt = True

                    else:
                        incorrect_next_evt = False

                    next_evt_idx += 1

                # Apply some conditioning to determine whether carry criteria is satisfied
                same_team = prev_evt_team == next_evt['teamId']
                not_ball_touch = match_event['type'] != 'BallTouch'
                dx = 105*(match_event['endX'] - next_evt['x'])/100
                dy = 68*(match_event['endY'] - next_evt['y'])/100
                far_enough = dx ** 2 + dy ** 2 >= min_carry_length ** 2
                not_too_far = dx ** 2 + dy ** 2 <= max_carry_length ** 2
                dt = 60 * (next_evt['cumulative_mins'] - match_event['cumulative_mins'])
                min_time = dt >= min_carry_duration
                same_phase = dt < max_carry_duration
                same_period = match_event['period'] == next_evt['period']

                valid_carry = same_team & not_ball_touch & far_enough & not_too_far & min_time & same_phase &same_period

                if valid_carry:
                    carry = pd.DataFrame()
                    prev = match_event
                    nex = next_evt

                    carry.loc[0, 'eventId'] = prev['eventId'] + 0.5
                    carry['minute'] = np.floor(((init_next_evt['minute'] * 60 + init_next_evt['second']) + (
                            prev['minute'] * 60 + prev['second'])) / (2 * 60))
                    carry['second'] = (((init_next_evt['minute'] * 60 + init_next_evt['second']) +
                                        (prev['minute'] * 60 + prev['second'])) / 2) - (carry['minute'] * 60)
                    carry['teamId'] = nex['teamId']
                    carry['x'] = prev['endX']
                    carry['y'] = prev['endY']
                    carry['expandedMinute'] = np.floor(((init_next_evt['expandedMinute'] * 60 + init_next_evt['second']) +
                                                        (prev['expandedMinute'] * 60 + prev['second'])) / (2 * 60))
                    carry['period'] = nex['period']
                    carry['type'] = carry.apply(lambda x: {'value': 99, 'displayName': 'Carry'}, axis=1)
                    carry['outcomeType'] = 'Successful'
                    carry['qualifiers'] = carry.apply(lambda x: {'type': {'value': 999, 'displayName': 'takeOns'}, 'value': str(take_ons)}, axis=1)
                    carry['satisfiedEventsTypes'] = carry.apply(lambda x: [], axis=1)
                    carry['isTouch'] = True
                    carry['playerId'] = nex['playerId']
                    carry['endX'] = nex['x']
                    carry['endY'] = nex['y']
                    carry['blockedX'] = np.nan
                    carry['blockedY'] = np.nan
                    carry['goalMouthZ'] = np.nan
                    carry['goalMouthY'] = np.nan
                    carry['isShot'] = np.nan
                    carry['relatedEventId'] = nex['eventId']
                    carry['relatedPlayerId'] = np.nan
                    carry['isGoal'] = np.nan
                    carry['cardType'] = np.nan
                    carry['isOwnGoal'] = np.nan
                    carry['type'] = 'Carry'
                    carry['cumulative_mins'] = (prev['cumulative_mins'] + init_next_evt['cumulative_mins']) / 2

                    match_carries = pd.concat([match_carries, carry], ignore_index=True, sort=False)

        match_events_and_carries = pd.concat([match_carries, match_events], ignore_index=True, sort=False)
        match_events_and_carries = match_events_and_carries.sort_values(['period', 'cumulative_mins']).reset_index(drop=True)

        # Rebuild events dataframe
        events_out = pd.concat([events_out, match_events_and_carries])

        return events_out

    df = insert_ball_carries(df, min_carry_length=3, max_carry_length=60, min_carry_duration=1, max_carry_duration=10)

    df = df.reset_index(drop=True)
    df['index'] = range(1, len(df) + 1)
    df = df[['index'] + [col for col in df.columns if col != 'index']]

    df['prog_pass'] = np.where((df['type'] == 'Pass'), 
                            np.sqrt((105 - df['x'])**2 + (34 - df['y'])**2) - np.sqrt((105 - df['endX'])**2 + (34 - df['endY'])**2), 0)
    df['prog_carry'] = np.where((df['type'] == 'Carry'), 
                                np.sqrt((105 - df['x'])**2 + (34 - df['y'])**2) - np.sqrt((105 - df['endX'])**2 + (34 - df['endY'])**2), 0)
    df['pass_or_carry_angle'] = np.degrees(np.arctan2(df['endY'] - df['y'], df['endX'] - df['x']))

    # New Column for Team Names and Oppositon TeamNames
    df['teamName'] = df['teamId'].map(teams_dict)
    team_names = list(teams_dict.values())
    opposition_dict = {team_names[i]: team_names[1-i] for i in range(len(team_names))}
    df['oppositionTeamName'] = df['teamName'].map(opposition_dict)

    def list_teams_from_df(players_df, teams_dict):
        def get_team_name_by_id(team_id, teams_dict):
            """Team ID'ye göre takım ismini döndürür."""
            return teams_dict.get(team_id, "Bilinmeyen Takım")
        
        # players_df'den ev sahibi ve deplasman takımlarını bulma
        teams = players_df['teamId'].unique()  # Benzersiz takım ID'lerini alıyoruz
        
        if len(teams) != 2:
            print("Verilerde ev sahibi ve deplasman takımları tam olarak bulunamadı.")
            return None, None, None, None
        
        home_team_id = teams[0]  # İlk takım ev sahibi
        away_team_id = teams[1]  # İkinci takım deplasman
        
        home_team_name = get_team_name_by_id(home_team_id, teams_dict)
        away_team_name = get_team_name_by_id(away_team_id, teams_dict)
        
        return home_team_id, home_team_name, away_team_id, away_team_name

    # Takımları al
    home_team_id, home_team_name, away_team_id, away_team_name = list_teams_from_df(players_df, teams_dict)

    pitch_color = '#d6c39f'
    dominate_pitch_color = '#808080'
    line_color = '#0e1117'
    second_line_color = '#38435c'
    green = '#1e7818'
    orange = '#ff5d44'
    blue = '#3572A5'
    red = '#ad1e11'
    yellow = '#c2a51d'
    dark_yellow = '#8a7512'
    gray = '#808080'
    dark_gray = '#626262'
    purple = '#3a1878'
    transparent_color = '#FFFFFF00'
    white_blue = '#c7ebf0'
    white_green = '#c7f0dd'

    def get_passes_df(df):
        df1 = df[~df['type'].str.contains('SubstitutionOn|FormationChange|FormationSet|Card')]
        df = df1
        df = df.copy()
        df.loc[:, "receiver"] = df["playerId"].shift(-1)
        passes_ids = df.index[df['type'] == 'Pass']
        df_passes = df.loc[passes_ids, ["index", "x", "y", "endX", "endY", "teamName", "playerId", "receiver", "type", "outcomeType", "pass_or_carry_angle"]]

        return df_passes

    passes_df = get_passes_df(df)
    path_eff = [path_effects.Stroke(linewidth=3, foreground=pitch_color), path_effects.Normal()]

    def get_passes_between_df(teamName, passes_df, players_df):
        # Takımın pas verilerini filtreleme
        passes_df = passes_df[(passes_df["teamName"] == teamName)]
        dfteam = df[(df['teamName'] == teamName)]

        # Oyuncu verileriyle birleştirme
        passes_df = passes_df.merge(players_df[["playerId", "isFirstEleven"]], on='playerId', how='left')

        # Ağırlıklı ortalama pozisyon hesaplama (pas sayısına göre)
        average_locs_and_count_df = dfteam.groupby('playerId').agg(
            pass_avg_x=('x', 'mean'),  # Medyan yerine ortalama
            pass_avg_y=('y', 'mean'),
            count=('y', 'count')  # Her oyuncunun pas sayısı
        )

        # Oyuncu bilgileriyle birleştirme
        average_locs_and_count_df = average_locs_and_count_df.merge(
            players_df[['playerId', 'name', 'shirtNo', 'position', 'isFirstEleven']], 
            on='playerId', 
            how='left'
        )

        # DataFrame'in son hali (oyuncuların ID'lerine göre index)
        average_locs_and_count_df = average_locs_and_count_df.set_index('playerId')

        # İsimlerin normalize edilmesi
        average_locs_and_count_df['name'] = average_locs_and_count_df['name'].apply(unidecode)
        # calculate the number of passes between each position (using min/ max so we get passes both ways)
        passes_player_ids_df = passes_df.loc[:, ['index', 'playerId', 'receiver', 'teamName']]
        passes_player_ids_df['pos_max'] = (passes_player_ids_df[['playerId', 'receiver']].max(axis='columns'))
        passes_player_ids_df['pos_min'] = (passes_player_ids_df[['playerId', 'receiver']].min(axis='columns'))
        # get passes between each player
        passes_between_df = passes_player_ids_df.groupby(['pos_min', 'pos_max']).index.count().reset_index()
        passes_between_df.rename({'index': 'pass_count'}, axis='columns', inplace=True)
        # add on the location of each player so we have the start and end positions of the lines
        passes_between_df = passes_between_df.merge(average_locs_and_count_df, left_on='pos_min', right_index=True)
        passes_between_df = passes_between_df.merge(average_locs_and_count_df, left_on='pos_max', right_index=True, suffixes=['', '_end'])
        passes_between_df = passes_between_df[passes_between_df['isFirstEleven_end'] == True]
        average_locs_and_count_df = average_locs_and_count_df[average_locs_and_count_df['isFirstEleven'] == True]
        #print(passes_between_df)
        #print(average_locs_and_count_df)
        return passes_between_df, average_locs_and_count_df

    # home_team_id = list(teams_dict.keys())[0]
    home_passes_between_df, home_average_locs_and_count_df = get_passes_between_df(home_team_name, passes_df, players_df)
    away_passes_between_df, away_average_locs_and_count_df = get_passes_between_df(away_team_name, passes_df, players_df)

    def match_details(ax):
        hometeamurl = f"https://images.fotmob.com/image_resources/logo/teamlogo/{homeTeamId}.png"
        awayteamurl = f"https://images.fotmob.com/image_resources/logo/teamlogo/{awayTeamId}.png"
        
        hometeam_logo = Image.open(BytesIO(requests.get(hometeamurl).content)).convert("RGBA")
        awayteam_logo = Image.open(BytesIO(requests.get(awayteamurl).content)).convert("RGBA")
        
        # Görseli küçültmek için OffsetImage kullanıyoruz
        home_imagebox = OffsetImage(hometeam_logo, zoom=0.3) 
        away_imagebox = OffsetImage(awayteam_logo, zoom=0.3) 

        # Görseli ortalamak için bir koordinat belirliyoruz
        x_center = (ax.get_xlim()[0] + ax.get_xlim()[1]) / 2
        y_center = (ax.get_ylim()[0] + ax.get_ylim()[1]) / 1.15

        # Görseli bu koordinata yerleştiriyoruz
        home = AnnotationBbox(home_imagebox, (x_center/2, y_center), frameon=False)
        away = AnnotationBbox(away_imagebox, (x_center*1.5, y_center), frameon=False)

        # Görseli eksene ekliyoruz
        ax.add_artist(home)
        ax.add_artist(away)
        
        top_stats = fotmobData['content']['stats']['Periods']['All']['stats'][0]['stats']
        pass_stats = fotmobData['content']['stats']['Periods']['All']['stats'][3]['stats']
        
        # Key'e göre veri çekme
        ball_possession = next(item['stats'] for item in top_stats if item['key'] == 'BallPossesion')
        expected_goals = next(item['stats'] for item in top_stats if item['key'] == 'expected_goals')
        total_shots = next(item['stats'] for item in top_stats if item['key'] == 'total_shots')
        shots_on_target = next(item['stats'] for item in top_stats if item['key'] == 'ShotsOnTarget')
        big_chances = next(item['stats'] for item in top_stats if item['key'] == 'big_chance')
        big_chances_missed = next(item['stats'] for item in top_stats if item['key'] == 'big_chance_missed_title')
        touches_in_opposition_box = next(item['stats'] for item in pass_stats if item['key'] == 'touches_opp_box')
        accurate_passes = next(item['stats'] for item in top_stats if item['key'] == 'accurate_passes')
        fouls_committed = next(item['stats'] for item in top_stats if item['key'] == 'fouls')
        corners = next(item['stats'] for item in top_stats if item['key'] == 'corners')

        # Değişkenlere atama
        ball_possession_home, ball_possession_away = ball_possession
        expected_goals_home, expected_goals_away = expected_goals
        total_shots_home, total_shots_away = total_shots
        shots_on_target_home, shots_on_target_away = shots_on_target
        big_chances_home, big_chances_away = big_chances
        big_chances_missed_home, big_chances_missed_away = big_chances_missed
        touches_in_opposition_box_home, touches_in_opposition_box_away = touches_in_opposition_box
        accurate_passes_home, accurate_passes_away = accurate_passes
        fouls_committed_home, fouls_committed_away = fouls_committed
        corners_home, corners_away = corners
        
        back_box = dict(boxstyle='round, pad=0.4', facecolor=to_rgba(blue, alpha=0.3), alpha=0.5)
        back_box_2 = dict(boxstyle='round, pad=0.4', facecolor=to_rgba(blue, alpha=0.3), alpha=0.2)
        
        ax.text(x_center, 0.65, "Gol Beklentisi (xG)", size=10, ha="center", fontproperties=prop, bbox=back_box, color='black')
        ax.text(x_center, 0.55, "Toplam Şut", size=10, ha="center", fontproperties=prop, bbox=back_box, color='black')
        ax.text(x_center, 0.45, "İsabetli Şut", size=10, ha="center", fontproperties=prop, bbox=back_box, color='black')
        ax.text(x_center, 0.35, "Gol Pozisyonu", size=10, ha="center", fontproperties=prop, bbox=back_box, color='black')
        ax.text(x_center, 0.25, "RCS Topla Oynama", size=10, ha="center", fontproperties=prop, bbox=back_box, color='black')
        ax.text(x_center, 0.15, "Başarılı Pas", size=10, ha="center", fontproperties=prop, bbox=back_box, color='black')
        ax.text(x_center, 0.05, "Topla Oynama", size=10, ha="center", fontproperties=prop, bbox=back_box, color='black')
        
        ax.text(x_center/2, 0.65, expected_goals_home, size=11, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
        ax.text(x_center/2, 0.55, total_shots_home, size=11, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
        ax.text(x_center/2, 0.45, shots_on_target_home, size=11, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
        ax.text(x_center/2, 0.35, big_chances_home, size=11, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
        ax.text(x_center/2, 0.25, touches_in_opposition_box_home, size=11, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
        ax.text(x_center/2, 0.15, accurate_passes_home, size=11, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
        ax.text(x_center/2, 0.05, f"{ball_possession_home}%", size=11, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
        
        ax.text(x_center*1.5, 0.65, expected_goals_away, size=11, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
        ax.text(x_center*1.5, 0.55, total_shots_away, size=11, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
        ax.text(x_center*1.5, 0.45, shots_on_target_away, size=11, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
        ax.text(x_center*1.5, 0.35, big_chances_away, size=11, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
        ax.text(x_center*1.5, 0.25, touches_in_opposition_box_away, size=11, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
        ax.text(x_center*1.5, 0.15, accurate_passes_away, size=11, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
        ax.text(x_center*1.5, 0.05, f"{ball_possession_away}%", size=11, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
        
        # Arka plan rengi ve eksenleri kapatma
        ax.set_facecolor(pitch_color)
        ax.axis('off')
        
    def shotmap(ax):
        pitch = Pitch(pitch_type='uefa', pitch_color=pitch_color, line_color=line_color, goal_type="line", corner_arcs=True)
        pitch.draw(ax=ax)
        #ax.set_xlim(-0.5,105.5)
        ax.set_ylim(-15,68.5)
        plt.axis('off')
        
        hometeamurl = f"https://images.fotmob.com/image_resources/logo/teamlogo/{homeTeamId}.png"
        awayteamurl = f"https://images.fotmob.com/image_resources/logo/teamlogo/{awayTeamId}.png"
        
        hometeam_logo = Image.open(BytesIO(requests.get(hometeamurl).content)).convert("RGBA")
        awayteam_logo = Image.open(BytesIO(requests.get(awayteamurl).content)).convert("RGBA")
        
        # Görseli küçültmek için OffsetImage kullanıyoruz
        home_imagebox = OffsetImage(hometeam_logo, zoom=0.1, alpha=0.5) 
        away_imagebox = OffsetImage(awayteam_logo, zoom=0.1, alpha=0.5) 

        # Görseli ortalamak için bir koordinat belirliyoruz
        x_center = (ax.get_xlim()[0] + ax.get_xlim()[1]) / 2

        # Görseli bu koordinata yerleştiriyoruz
        home = AnnotationBbox(home_imagebox, (x_center/8, 5), frameon=False)
        away = AnnotationBbox(away_imagebox, (x_center*1.875, 5), frameon=False)

        # Görseli eksene ekliyoruz
        ax.add_artist(home)
        ax.add_artist(away)
        
        arrow_home = FancyArrowPatch((x_center/8+4, 5), (x_center/8+16, 5), color=homeColor, linewidth=1, arrowstyle='->', mutation_scale=12, alpha=0.5)
        ax.add_patch(arrow_home)
        
        arrow_away = FancyArrowPatch((x_center*1.875-16, 5), (x_center*1.875-4, 5), color=awayColor, linewidth=1, arrowstyle='<-', mutation_scale=12, alpha=0.5)
        ax.add_patch(arrow_away)
        
        goal_color = green
        saved_color = blue
        blocked_color = '#40427a'
        miss_color = 'red'
        post_color = gray  # Direkten dönen şutlar koyu gri
            
        home_shots = [shot for shot in shots_data if shot['teamId'] == homeTeamId]
        away_shots = [shot for shot in shots_data if shot['teamId'] == awayTeamId]
        
        for shot in away_shots:
            shot['x'] = 105 - shot['x']
            shot['y'] = 68 - shot['y']
            shot['goalCrossedY'] = 68 - shot['goalCrossedY']
            if shot['blockedX']:
                shot['blockedX'] = 105 - shot['blockedX']
            if shot['blockedY']:
                shot['blockedY'] = 68 - shot['blockedY']
        
        if home_shots:
            # Seçilen oyuncunun şut haritasını çiz
            for shot in home_shots:
                if shot['isOwnGoal'] != True:
                    if shot['eventType'] == 'Goal':  # Gol olan şut
                        shot_color = goal_color
                        #pitch.lines(shot['x'], shot['y'], 105, shot['goalCrossedY'], ax=ax, color=to_rgba(shot_color, alpha=0.5), lw=1)
                        pitch.scatter(shot['x'], shot['y'], ax=ax, c='None', s=round(shot['expectedGoals'], 2)*750, edgecolors=goal_color, marker='football', alpha=0.8)
                    
                    elif shot['eventType'] == 'AttemptSaved' and shot['isBlocked'] == True and shot['expectedGoalsOnTarget'] == 0:  # Bloklanan şut
                        shot_color = blocked_color
                        #pitch.lines(shot['x'], shot['y'], shot['blockedX'], shot['blockedY'], ax=ax, color=to_rgba(shot_color, alpha=0.5), lw=1)
                        pitch.scatter(shot['x'], shot['y'], ax=ax, c=shot_color, s=round(shot['expectedGoals'], 2)*750, edgecolors='white', marker='D', alpha=0.8, lw=0.7, hatch='|||||')
                    
                    elif shot['eventType'] == 'AttemptSaved' and shot['isBlocked'] == False:  # İsabetli Şut | Kurtarılan şut
                        shot_color = saved_color
                        #pitch.lines(shot['x'], shot['y'], shot['blockedX'], shot['blockedY'], ax=ax, color=to_rgba(shot_color, alpha=0.5), lw=1)
                        pitch.scatter(shot['x'], shot['y'], ax=ax, c=shot_color, s=round(shot['expectedGoals'], 2)*750, edgecolors='white', marker='o', alpha=0.8, lw=1, hatch='/////')
                    
                    elif shot['eventType'] == 'Miss':  # İsabetsiz şut
                        shot_color = miss_color
                        #pitch.lines(shot['x'], shot['y'], 105, shot['goalCrossedY'], ax=ax, color=to_rgba(shot_color, alpha=0.25), lw=1)
                        pitch.scatter(shot['x'], shot['y'], ax=ax, c=shot_color, s=round(shot['expectedGoals'], 2)*750, edgecolors='black', marker='x', alpha=0.8, lw=1)
                    
                    elif shot['eventType'] == 'Post':  # Direkten dönen şut
                        shot_color = post_color
                        #pitch.lines(shot['x'], shot['y'], 105, shot['goalCrossedY'], ax=ax, color=to_rgba(shot_color, alpha=0.25), lw=1)
                        pitch.scatter(shot['x'], shot['y'], ax=ax, c=shot_color, s=round(shot['expectedGoals'], 2)*750, edgecolors='black', marker='+', alpha=0.8, lw=1, hatch='|')
                    
                    else:  # Bloklanan diğer şutlar
                        shot_color = blocked_color
                        #pitch.lines(shot['x'], shot['y'], shot['blockedX'], shot['blockedY'], ax=ax, color=to_rgba(shot_color, alpha=0.5), lw=1)
                        pitch.scatter(shot['x'], shot['y'], ax=ax, c=shot_color, s=round(shot['expectedGoals'], 2)*750, edgecolors='black', marker='o', alpha=0.8, lw=1, hatch='/')
                    
        if away_shots:
            # Seçilen oyuncunun şut haritasını çiz
            for shot in away_shots:
                if shot['isOwnGoal'] != True:
                    if shot['eventType'] == 'Goal':  # Gol olan şut
                        shot_color = goal_color
                        #pitch.lines(shot['x'], shot['y'], 0, shot['goalCrossedY'], ax=ax, color=to_rgba(shot_color, alpha=0.5), lw=1)
                        pitch.scatter(shot['x'], shot['y'], ax=ax, c='None', s=round(shot['expectedGoals'], 2)*750, edgecolors=goal_color, marker='football', alpha=0.8)
                    
                    elif shot['eventType'] == 'AttemptSaved' and shot['isBlocked'] == True and shot['expectedGoalsOnTarget'] == 0:  # Bloklanan şut
                        shot_color = blocked_color
                        #pitch.lines(shot['x'], shot['y'], shot['blockedX'], shot['blockedY'], ax=ax, color=to_rgba(shot_color, alpha=0.5), lw=1)
                        pitch.scatter(shot['x'], shot['y'], ax=ax, c=shot_color, s=round(shot['expectedGoals'], 2)*750, edgecolors='white', marker='D', alpha=0.8, lw=0.7, hatch='|||||')
                    
                    elif shot['eventType'] == 'AttemptSaved' and shot['isBlocked'] == False:  # İsabetli Şut | Kurtarılan şut
                        shot_color = saved_color
                        #pitch.lines(shot['x'], shot['y'], shot['blockedX'], shot['blockedY'], ax=ax, color=to_rgba(shot_color, alpha=0.5), lw=1)
                        pitch.scatter(shot['x'], shot['y'], ax=ax, c=shot_color, s=round(shot['expectedGoals'], 2)*750, edgecolors='white', marker='o', alpha=0.8, lw=1, hatch='/////')
                    
                    elif shot['eventType'] == 'Miss':  # İsabetsiz şut
                        shot_color = miss_color
                        #pitch.lines(shot['x'], shot['y'], 0, shot['goalCrossedY'], ax=ax, color=to_rgba(shot_color, alpha=0.25), lw=1)
                        pitch.scatter(shot['x'], shot['y'], ax=ax, c=shot_color, s=round(shot['expectedGoals'], 2)*750, edgecolors='black', marker='x', alpha=0.8, lw=1)
                    
                    elif shot['eventType'] == 'Post':  # Direkten dönen şut
                        shot_color = post_color
                        #pitch.lines(shot['x'], shot['y'], 0, shot['goalCrossedY'], ax=ax, color=to_rgba(shot_color, alpha=0.25), lw=1)
                        pitch.scatter(shot['x'], shot['y'], ax=ax, c=shot_color, s=round(shot['expectedGoals'], 2)*750, edgecolors='black', marker='+', alpha=0.8, lw=1, hatch='|')
                    
                    else:  # Bloklanan diğer şutlar
                        shot_color = blocked_color
                        #pitch.lines(shot['x'], shot['y'], shot['blockedX'], shot['blockedY'], ax=ax, color=to_rgba(shot_color, alpha=0.5), lw=1)
                        pitch.scatter(shot['x'], shot['y'], ax=ax, c=shot_color, s=round(shot['expectedGoals'], 2)*750, edgecolors='black', marker='o', alpha=0.8, lw=1, hatch='/')
        
        pitch.scatter(2.2, -5, ax=ax, c='None', s=200, edgecolors=goal_color, marker='football', alpha=0.8)
        ax.text(5.2, -5.5, ": Gol  |", fontsize=12, ha='left', va='center', fontproperties=prop)
        
        pitch.scatter(21.7, -5, ax=ax, c=saved_color, s=200, edgecolors='white', marker='o', alpha=0.8, lw=1, hatch='/////')
        ax.text(25, -5.5, ": Kurtarılan Şut  |", fontsize=12, ha='left', va='center', fontproperties=prop)
        
        pitch.scatter(62.4, -5, ax=ax, c=blocked_color, s=125, edgecolors='white', marker='D', alpha=0.8, lw=0.7, hatch='|||||')
        ax.text(65.5, -5.5, ": Bloklanan Şut", fontsize=12, ha='left', va='center', fontproperties=prop)
        
        pitch.scatter(2.2, -12, ax=ax, c=post_color, s=200, edgecolors='black', marker='+', alpha=0.8, lw=1, hatch='|')
        ax.text(5.2, -12.5, ": Direkten Dönen Şut  |", fontsize=12, ha='left', va='center', fontproperties=prop)
        
        pitch.scatter(53.5, -12, ax=ax, c=miss_color, s=100, edgecolors='black', marker='x', alpha=0.8, lw=1)
        ax.text(56.5, -12.5, ": İsabetsiz Şut", fontsize=12, ha='left', va='center', fontproperties=prop)
        
        ax.set_title(f"Şut Haritası", color=line_color, fontproperties=bold_prop, fontweight='bold', y=1.05)
        
        return

    def momentum(ax):
        # Arka plan rengi ve eksenleri kapatma
        ax.set_facecolor(pitch_color)
        ax.axis('off')
        
        ax.set_ylim(-200, 200)  # Y eksen sınırlarını ayarla
        
        momentum_data = fotmobData['content']['momentum']['main']['data']
        minutes = [item['minute'] for item in momentum_data]
        values = [item['value'] for item in momentum_data]
        
        match_events_data = fotmobData['content']['matchFacts']['events']['events']
        # Gol olaylarını filtrele
        goal_events = [event for event in match_events_data if event['type'] == 'Goal']
        card_events = [event for event in match_events_data if event['type'] == 'Card']
        redcard_events = [event for event in card_events if (event['card'] == 'Red') or (event['card'] == 'YellowRed')]
        
        # Gol dakikalarını ve hangi takımın attığını bulma
        goal_minutes = [event['time'] for event in goal_events]
        is_home_goal = [event['isHome'] for event in goal_events]
        
        redcard_minutes = [redcardevent['time'] for redcardevent in redcard_events]
        is_home_redcard = [redcardevent['isHome'] for redcardevent in redcard_events]
        
        # Pozitif değerler (ev sahibi takım)
        ax.fill_between(minutes, values, 0, where=[v > 0 for v in values], color=homeColor, alpha=0.6, zorder=8)

        # Negatif değerler (deplasman takımı)
        ax.fill_between(minutes, values, 0, where=[v < 0 for v in values], color=awayColor, alpha=0.6, zorder=8)
        
        ax.axhline(0, color=line_color, linewidth=1, alpha=0.7)
        
        football_img = mpimg.imread('icons/ball.png')
        imagebox = OffsetImage(football_img, zoom=0.3)  # Görselin boyutunu ayarlamak için zoom kullanın
        
        redcard_img = mpimg.imread('icons/redcard.png')
        redcard_imagebox = OffsetImage(redcard_img, zoom=0.175)  # Görselin boyutunu ayarlamak için zoom kullanın

        # Golleri işaretleme (ev sahibi ve deplasman için farklı yerlerde)
        for i, minute in enumerate(goal_minutes):
            x = minute
            if is_home_goal[i]:  # Ev sahibi gol attıysa
                y = 140  # Ev sahibi takım için üstte yerleştir
            else:  # Deplasman gol attıysa
                y = -140  # Deplasman takım için altta yerleştir
            
            # AnnotationBbox ile görseli ekleme
            ab = AnnotationBbox(imagebox, (x, y), frameon=False)  # Görseli belirli bir konuma ekleyin
            ax.add_artist(ab)
            
        # Golleri işaretleme (ev sahibi ve deplasman için farklı yerlerde)
        for i, minute in enumerate(redcard_minutes):
            x = minute
            if is_home_redcard[i]:  # Ev sahibi gol attıysa
                y = 140  # Ev sahibi takım için üstte yerleştir
            else:  # Deplasman gol attıysa
                y = -140  # Deplasman takım için altta yerleştir
            
            # AnnotationBbox ile görseli ekleme
            ab = AnnotationBbox(redcard_imagebox, (x, y), frameon=False)  # Görseli belirli bir konuma ekleyin
            ax.add_artist(ab)

        # HT ve FT işaretlemeleri
        # Başlangıç dakikası
        start_minute = 0
        # İlk yarı sonu ve maç sonu
        ht_minute = max([item['minute'] for item in momentum_data if item['minute'] < 46], default=45.75)
        ft_minute = max([item['minute'] for item in momentum_data if item['minute'] > 45], default=90.75)
        
        # Start işareti
        ax.text(start_minute, -190, '0', color='black', ha='center', va='bottom', fontsize=10, fontproperties=prop)

        # HT işareti
        ax.plot([ht_minute, ht_minute], [-160, 170], color='black', linestyle='--', linewidth=1, alpha=0.25, zorder=1)
        ax.text(ht_minute, -190, 'İY', color='black', ha='center', va='bottom', fontsize=10, fontproperties=prop)
        
        # FT işareti
        ax.text(ft_minute, -190, 'MS', color='black', ha='center', va='bottom', fontsize=10, fontproperties=prop)
        
        # Grafiğin altına uzun kesik çizgi ekleme
        ax.axhline(y=-160, color='black', linestyle='--', linewidth=1, xmin=0, xmax=1, alpha=0.25)
        
        hometeamurl = f"https://images.fotmob.com/image_resources/logo/teamlogo/{homeTeamId}.png"
        awayteamurl = f"https://images.fotmob.com/image_resources/logo/teamlogo/{awayTeamId}.png"
        
        hometeam_logo = Image.open(BytesIO(requests.get(hometeamurl).content)).convert("RGBA")
        awayteam_logo = Image.open(BytesIO(requests.get(awayteamurl).content)).convert("RGBA")
        
        # Görseli küçültmek için OffsetImage kullanıyoruz
        home_imagebox = OffsetImage(hometeam_logo, zoom=0.15, alpha=0.5) 
        away_imagebox = OffsetImage(awayteam_logo, zoom=0.15, alpha=0.5) 

        # Görseli bu koordinata yerleştiriyoruz
        home = AnnotationBbox(home_imagebox, (3, 85), frameon=False)
        away = AnnotationBbox(away_imagebox, (3, -80), frameon=False)

        # Görseli eksene ekliyoruz
        ax.add_artist(home)
        ax.add_artist(away)
        
        ax.set_title(f"Momentum", color=line_color, fontproperties=bold_prop, fontweight='bold', y=1.002)
        
        return

    def pass_network_visualization(ax, passes_between_df, average_locs_and_count_df, col, teamName, flipped=False): 
        MAX_LINE_WIDTH = 15
        MAX_MARKER_SIZE = 3000
        passes_between_df = passes_between_df[passes_between_df['isFirstEleven'] == True].copy()
        passes_between_df['width'] = (passes_between_df.pass_count / passes_between_df.pass_count.max() *MAX_LINE_WIDTH)
        # average_locs_and_count_df['marker_size'] = (average_locs_and_count_df['count']/ average_locs_and_count_df['count'].max() * MAX_MARKER_SIZE) #You can plot variable size of each player's node according to their passing volume, in the plot using this
        MIN_TRANSPARENCY = 0.05
        MAX_TRANSPARENCY = 0.85
        color = np.array(to_rgba(col))
        color = np.tile(color, (len(passes_between_df), 1))
        c_transparency = passes_between_df.pass_count / passes_between_df.pass_count.max()
        c_transparency = (c_transparency * (MAX_TRANSPARENCY - MIN_TRANSPARENCY)) + MIN_TRANSPARENCY
        color[:, 3] = c_transparency

        pitch = Pitch(pitch_type='uefa', corner_arcs=True, pitch_color=pitch_color, line_color=line_color, linewidth=2, goal_type="line")
        pitch.draw(ax=ax)
        # Initial setup
        ax.set_xlim(-0.5, 105.5)
        ax.set_ylim(-0.5, 68.5)

        # Invert axes for away team
        if teamName == away_team_name:
            ax.invert_xaxis()
            ax.invert_yaxis()
            #ax.set_xlim(105.5, -0.5)  # Adjust x-limits after inversion
            ax.set_ylim(68.5, -0.5)   # Adjust y-limits after inversion
            text_x = 105.5  # Example x position for away team
            text_y = 72.5  # Example y position for away team
            annotate_padding = -0.4
            def_line_ha_team_width = 'left'
            def_line_ha_team_height = 'right'
            def_line_text_y = 63
            team_width_height_color = awayColor
        else:
            text_x = 0
            text_y = -4
            annotate_padding = 0.4
            def_line_ha_team_width = 'right'
            def_line_ha_team_height = 'left'
            def_line_text_y = 5
            team_width_height_color = homeColor

        # Plotting those lines between players
        pass_lines = pitch.lines(passes_between_df.pass_avg_x, passes_between_df.pass_avg_y, passes_between_df.pass_avg_x_end, passes_between_df.pass_avg_y_end,
                                lw=passes_between_df.width, color=color, zorder=1, ax=ax)
        
        scatter_zorder = 2

        for index, row in average_locs_and_count_df.iterrows():
            if row['isFirstEleven']:
                # Oyuncu noktası
                pitch.scatter(
                    row['pass_avg_x'], row['pass_avg_y'],
                    s=600, marker='o', color=pitch_color,
                    edgecolor=line_color, linewidth=2, alpha=1,
                    ax=ax, zorder=scatter_zorder
                )

                # Forma numarası
                pitch.annotate(
                    row["shirtNo"],
                    xy=(row.pass_avg_x, row.pass_avg_y - annotate_padding),
                    c=col, ha='center', va='center', size=14,
                    ax=ax, fontproperties=prop,
                    zorder=scatter_zorder + 1
                )

                scatter_zorder += 2  # her iki öğe için sıralamayı koru

                
        # Plotting a vertical line to show the median vertical position of all passes
        avgph = round(average_locs_and_count_df['pass_avg_x'].median(), 2)
        # avgph_show = round((avgph*1.05),2)
        avgph_show = avgph
        ax.axvline(x=avgph, color='gray', linestyle='--', alpha=0.75, linewidth=2)

        # Defense line Passing Height (avg. height of all the passes made by the Center Backs)
        center_backs_height = average_locs_and_count_df[average_locs_and_count_df['position']!='GK']
        center_backs_height = center_backs_height.sort_values(by='pass_avg_x', ascending=True)
        center_backs_height = center_backs_height.head(1)
        def_line_h = round(center_backs_height['pass_avg_x'].median(), 2)
        ax.axvline(x=def_line_h, color='gray', linestyle='dotted', alpha=0.5, linewidth=2)
        
        # Forward line Passing Height (avg. height of all the passes made by the Top 2 avg positoned Forwards)
        Forwards_height = average_locs_and_count_df[average_locs_and_count_df['isFirstEleven']==1]
        Forwards_height = Forwards_height.sort_values(by='pass_avg_x', ascending=False)
        Forwards_height = Forwards_height.head(1)
        fwd_line_h = round(Forwards_height['pass_avg_x'].mean(), 2)
        ax.axvline(x=fwd_line_h, color='gray', linestyle='dotted', alpha=0.5, linewidth=2)
        
        # coloring the middle zone in the pitch
        ymid = [0, 0, 68, 68]
        xmid = [def_line_h, fwd_line_h, fwd_line_h, def_line_h]
        ax.fill(xmid, ymid, col, alpha=0.1)
        
        distance_between_lines = round(fwd_line_h - def_line_h, 2) #Takım boyu
        
        wide_players = average_locs_and_count_df[average_locs_and_count_df['isFirstEleven']==1]

        leftmost = wide_players.loc[wide_players['pass_avg_y'].idxmin()]
        rightmost = wide_players.loc[wide_players['pass_avg_y'].idxmax()]

        team_width = round(rightmost['pass_avg_y'] - leftmost['pass_avg_y'], 2) #Takım genişliği
        
        team_height_x = 3
        team_width_x = 102
        
        ax.text(team_width_x, def_line_text_y,  f'Takım Genişliği\n{team_width}m', size=8, style='italic', ha=def_line_ha_team_width, va="center", fontproperties=prop, color=team_width_height_color)
        ax.text(team_height_x, def_line_text_y, f'Takım Boyu\n{distance_between_lines}m', size=8, style='italic', ha=def_line_ha_team_height, va="center", fontproperties=prop, color=team_width_height_color)

        # Getting the top passers combination
        passes_between_df = passes_between_df.sort_values(by='pass_count', ascending=False).head(1).reset_index(drop=True)
        most_pass_from = passes_between_df['name'][0]
        most_pass_to = passes_between_df['name_end'][0]
        most_pass_count = passes_between_df['pass_count'][0]
        
        # Getting the verticality of a team, (Verticality means how straight forward a team passes while advancing the ball, more the value = more directness in forward passing)
        team_passes_df = passes_df[(passes_df["teamName"] == teamName)].copy()
        team_passes_df['pass_or_carry_angle'] = team_passes_df['pass_or_carry_angle'].abs()
        team_passes_df = team_passes_df[(team_passes_df['pass_or_carry_angle']>=0) & (team_passes_df['pass_or_carry_angle']<=90)]
        med_ang = team_passes_df['pass_or_carry_angle'].median()
        verticality = round((1 - med_ang/90)*100, 2)
        
        ax.set_title(f"{teamName} Pas Haritası", color=line_color, size=25, fontweight='bold', fontproperties=bold_prop, y=1.05)
        
        ax_text(text_x, text_y, f'''<En Yoğun Pas Bağlantısı: ><{most_pass_from} - {most_pass_to}>\n<Dikey Pas Oranı, Doğrudanlık: ><%{verticality}>
            ''', color=line_color, highlight_textprops=[{'color':line_color}, {'color':col}, {'color':line_color}, {'color':col}], fontsize=12, ha='left', va='top', ax=ax, fontproperties=prop)
        
        return

    def key_passes(ax):
        pitch = Pitch(pitch_type='uefa', pitch_color=pitch_color, line_color=line_color, goal_type="line", corner_arcs=True)
        pitch.draw(ax=ax)
        ax.set_xlim(-0.5,105.5)
        ax.set_ylim(-0.5,68.5)
        plt.axis('off')
        
        df.loc[:, 'qualifiers'] = df['qualifiers'].fillna('')
        df.loc[:, 'qualifiers'] = df['qualifiers'].astype(str)
        pass_events = df[df['type']=='Pass']
        # DataFrame'e dönüştürelim
        df_passes = pd.DataFrame(pass_events)
        
        df_key_passes = df_passes[df_passes['qualifiers'].str.contains('KeyPass')]
        home_key_passes = df_key_passes[df_key_passes['teamId'] == home_team_id].copy()
        away_key_passes = df_key_passes[df_key_passes['teamId'] == away_team_id].copy()
            
        away_key_passes['x'] = 105 - away_key_passes['x']
        away_key_passes['endX'] = 105 - away_key_passes['endX']
        away_key_passes['y'] = 68 - away_key_passes['y']
        away_key_passes['endY'] = 68 - away_key_passes['endY']
        
        key_pass_home = pitch.lines(home_key_passes["x"], home_key_passes["y"], home_key_passes["endX"], home_key_passes["endY"],
                                ax=ax, lw=2.5, transparent=True, comet=True,
                                label='Key Passes',color=homeColor, zorder=2)
        key_pass_home_2 = pitch.scatter(home_key_passes["endX"], home_key_passes["endY"], marker='o', s=20, c=pitch_color, edgecolor=homeColor,linewidth=1,zorder=2, ax=ax)
        
        key_pass_away = pitch.lines(away_key_passes["x"], away_key_passes["y"], away_key_passes["endX"], away_key_passes["endY"],
                                ax=ax, lw=2.5, transparent=True, comet=True,
                                label='Key Passes',color=awayColor, zorder=2)
        key_pass_away_2 = pitch.scatter(away_key_passes["endX"], away_key_passes["endY"], marker='o', s=20, c=pitch_color, edgecolor=awayColor, linewidth=1,zorder=2, ax=ax)
        
        x_center = (ax.get_xlim()[0] + ax.get_xlim()[1]) / 2
        y_center = (ax.get_ylim()[0] + ax.get_ylim()[1]) / 2
        
        x_margin = 5
        
        text_y_margin = 0.7
        
        top_y = 63
        center_y = 34
        bottom_y = 5
        
        home_key_passes_count = len(home_key_passes)
        away_key_passes_count = len(away_key_passes)
        
        ax.scatter(x_center-x_margin, top_y, s=750, marker='s', color=homeColor, zorder=3)
        ax.text(x_center-x_margin, top_y-text_y_margin, home_key_passes_count, fontsize=20, fontproperties=prop, fontweight='bold', color=pitch_color, ha='center', va='center')
        
        ax.scatter(x_center+x_margin, top_y, s=750, marker='s', color=awayColor, zorder=3)
        ax.text(x_center+x_margin, top_y-text_y_margin, away_key_passes_count, fontsize=20, fontproperties=prop, fontweight='bold', color=pitch_color, ha='center', va='center')
        
        hometeamurl = f"https://images.fotmob.com/image_resources/logo/teamlogo/{homeTeamId}.png"
        awayteamurl = f"https://images.fotmob.com/image_resources/logo/teamlogo/{awayTeamId}.png"
        
        hometeam_logo = Image.open(BytesIO(requests.get(hometeamurl).content)).convert("RGBA")
        awayteam_logo = Image.open(BytesIO(requests.get(awayteamurl).content)).convert("RGBA")
        
        # Görseli küçültmek için OffsetImage kullanıyoruz
        home_imagebox = OffsetImage(hometeam_logo, zoom=0.1, alpha=0.5) 
        away_imagebox = OffsetImage(awayteam_logo, zoom=0.1, alpha=0.5) 

        # Görseli bu koordinata yerleştiriyoruz
        home = AnnotationBbox(home_imagebox, (x_center/8, 5), frameon=False)
        away = AnnotationBbox(away_imagebox, (x_center*1.875, 5), frameon=False)

        # Görseli eksene ekliyoruz
        ax.add_artist(home)
        ax.add_artist(away)
        
        arrow_home = FancyArrowPatch((x_center/8+4, 5), (x_center/8+16, 5), color=homeColor, linewidth=1, arrowstyle='->', mutation_scale=12, alpha=0.5)
        ax.add_patch(arrow_home)
        
        arrow_away = FancyArrowPatch((x_center*1.875-16, 5), (x_center*1.875-4, 5), color=awayColor, linewidth=1, arrowstyle='<-', mutation_scale=12, alpha=0.5)
        ax.add_patch(arrow_away)
        
        ax.set_title(f"Kilit Pas Haritası", color=line_color, fontproperties=bold_prop, fontweight='bold', y=1.05)
        
        return

    def zone14andhalfspace(ax, team_name):
        dfhp = df[(df['teamName']==team_name) & (df['type']=='Pass') & (df['outcomeType']=='Successful') & 
                (~df['qualifiers'].str.contains('CornerTaken|Freekick'))]
        
        pitch = Pitch(pitch_type='uefa', corner_arcs=True, pitch_color=pitch_color, line_color=line_color, linewidth=2, goal_type="line")
        pitch.draw(ax=ax)
        ax.set_xlim(-0.5, 105.5)
        ax.set_facecolor(pitch_color)
        if team_name == away_team_name:
            ax.invert_xaxis()
            ax.invert_yaxis()
            col = awayColor
            ax.set_title(f"{away_team_name}\nZone14 & Half Space Pasları", color=line_color, fontweight='bold', fontproperties=bold_prop)
            text_padding = 2
            count_text_padding = 6
            zone14_text_padding = 3
        else:
            col = homeColor
            ax.set_title(f"{home_team_name}\nZone14 & Half Space Pasları", color=line_color, fontweight='bold', fontproperties=bold_prop)
            text_padding = -2
            count_text_padding = -6
            zone14_text_padding = -3

        # setting the count varibale
        z14 = 0
        hs = 0
        lhs = 0
        rhs = 0
        
        zone14_color = '#bd841c'
        alpha_value = 0.4

        path_eff = [path_effects.Stroke(linewidth=3, foreground=pitch_color), path_effects.Normal()]
        # iterating ecah pass and according to the conditions plotting only zone14 and half spaces passes
        for index, row in dfhp.iterrows():
            if row['endX'] >= 70 and row['endX'] <= 88.54 and row['endY'] >= 22.66 and row['endY'] <= 45.32:
                pitch.lines(row['x'], row['y'], row['endX'], row['endY'], color=zone14_color, transparent=True, comet=True, lw=3, zorder=3, ax=ax, alpha=alpha_value)
                ax.scatter(row['endX'], row['endY'], s=35, linewidth=1, color=pitch_color, edgecolor=zone14_color, zorder=4)
                z14 += 1
            if row['endX'] >= 70 and row['endY'] >= 11.33 and row['endY'] <= 22.66:
                pitch.lines(row['x'], row['y'], row['endX'], row['endY'], color=col, transparent=True, comet=True, lw=3, zorder=3, ax=ax, alpha=alpha_value)
                ax.scatter(row['endX'], row['endY'], s=35, linewidth=1, color=pitch_color, edgecolor=col, zorder=4)
                hs += 1
                rhs += 1
            if row['endX'] >= 70 and row['endY'] >= 45.32 and row['endY'] <= 56.95:
                pitch.lines(row['x'], row['y'], row['endX'], row['endY'], color=col, transparent=True, comet=True, lw=3, zorder=3, ax=ax, alpha=alpha_value)
                ax.scatter(row['endX'], row['endY'], s=35, linewidth=1, color=pitch_color, edgecolor=col, zorder=4)
                hs += 1
                lhs += 1

        # coloring those zones in the pitch
        y_z14 = [22.66, 22.66, 45.32, 45.32]
        x_z14 = [70, 88.54, 88.54, 70]
        ax.fill(x_z14, y_z14, zone14_color, alpha=0.2, label='Zone14')

        y_rhs = [11.33, 11.33, 22.66, 22.66]
        x_rhs = [70, 105, 105, 70]
        ax.fill(x_rhs, y_rhs, col, alpha=0.2, label='HalfSpaces')

        y_lhs = [45.32, 45.32, 56.95, 56.95]
        x_lhs = [70, 105, 105, 70]
        ax.fill(x_lhs, y_lhs, col, alpha=0.2, label='HalfSpaces')
        
        y_center = (ax.get_ylim()[0] + ax.get_ylim()[1]) / 2

        # showing the counts in an attractive way
        z14name = "Zone14"
        hsnameright = "Sağ Half\nSpace"
        hsnameleft = "Sol Half\nSpace"
        z14count = f"{z14}"
        hscount = f"{hs}"
        righthscount = f"{rhs}"
        lefthscount = f"{lhs}"
        
        ax.text(16.46, y_center+23+count_text_padding, lefthscount, fontsize=20, color=pitch_color, ha='center', va='center', fontproperties=bold_prop, fontweight='bold')
        ax.scatter(16.46, y_center+23, color=col, s=4000, edgecolor=line_color, linewidth=2, alpha=1, marker='h')
        ax.text(16.46, y_center+23-text_padding, hsnameleft, fontsize=10, color=pitch_color, ha='center', va='center', fontproperties=prop)
        
        ax.text(16.46, y_center+zone14_text_padding, z14count, fontsize=20, color=line_color, ha='center', va='center', fontproperties=bold_prop, fontweight='bold') 
        ax.scatter(16.46, y_center, color=zone14_color, s=2000, edgecolor=line_color, linewidth=2, alpha=1, marker='D')
        ax.text(16.46, y_center-text_padding, z14name, fontsize=10, color=line_color, ha='center', va='center', fontproperties=prop)
        
        ax.text(16.46, y_center-23+count_text_padding, righthscount, fontsize=20, color=pitch_color, ha='center', va='center', fontproperties=bold_prop, fontweight='bold')
        ax.scatter(16.46, y_center-23, color=col, s=4000, edgecolor=line_color, linewidth=2, alpha=1, marker='h')
        ax.text(16.46, y_center-23-text_padding, hsnameright, fontsize=10, color=pitch_color, ha='center', va='center', fontproperties=prop)

        return
        
    def box_entry(ax):
        # Box Entry means passes or carries which has started outside the Opponent Penalty Box and ended inside the Opponent Penalty Box 
        bentry = df[((df['type']=='Pass')|(df['type']=='Carry')) & (df['outcomeType']=='Successful') & (df['endX']>=88.5) &
                    ~((df['x']>=88.5) & (df['y']>=13.6) & (df['y']<=54.6)) & (df['endY']>=13.6) & (df['endY']<=54.4) &
                (~df['qualifiers'].str.contains('CornerTaken|Freekick|ThrowIn'))]
        hbentry = bentry[bentry['teamName']==home_team_name]
        abentry = bentry[bentry['teamName']==away_team_name]

        hrigt = hbentry[hbentry['y']<68/3]
        hcent = hbentry[(hbentry['y']>=68/3) & (hbentry['y']<=136/3)]
        hleft = hbentry[hbentry['y']>136/3]

        arigt = abentry[(abentry['y']<68/3)]
        acent = abentry[(abentry['y']>=68/3) & (abentry['y']<=136/3)]
        aleft = abentry[(abentry['y']>136/3)]

        pitch = Pitch(pitch_type='uefa', line_color=line_color, corner_arcs=True, line_zorder=2, pitch_color=pitch_color, linewidth=2, goal_type="line")
        pitch.draw(ax=ax)
        ax.set_xlim(-0.5, 105.5)
        ax.set_ylim(-0.5, 68.5)

        for index, row in bentry.iterrows():
            if row['teamName'] == home_team_name:
                color = homeColor
                x, y, endX, endY = row['x'], row['y'], row['endX'], row['endY']
            elif row['teamName'] == away_team_name:
                color = awayColor
                x, y, endX, endY = 105 - row['x'], 68 - row['y'], 105 - row['endX'], 68 - row['endY']
            else:
                continue  # Skip rows that don't match either team name

            if row['type'] == 'Pass':
                pitch.lines(x, y, endX, endY, lw=3.5, transparent=True, comet=True, color=color, ax=ax)
                pitch.scatter(endX, endY, s=35, edgecolor=color, linewidth=1, color=pitch_color, zorder=2, ax=ax)
            elif row['type'] == 'Carry':
                arrow = FancyArrowPatch((x, y), (endX, endY), arrowstyle='->', color=color, zorder=4, mutation_scale=20, 
                                                alpha=1, linewidth=2, linestyle='--')
                ax.add_patch(arrow)
                
        x_center = (ax.get_xlim()[0] + ax.get_xlim()[1]) / 2
        y_center = (ax.get_ylim()[0] + ax.get_ylim()[1]) / 2
        
        x_margin = 5
        
        text_y_margin = 0.7
        
        top_y = 63
        center_y = 34
        bottom_y = 5

        ax.scatter(x_center-x_margin, bottom_y, s=750, marker='o', color=homeColor, zorder=3)
        ax.text(x_center-x_margin, bottom_y-text_y_margin, f'{len(hleft)}', fontsize=20, fontproperties=prop, fontweight='bold', color=pitch_color, ha='center', va='center')
        
        ax.scatter(x_center-x_margin, y_center, s=750, marker='o', color=homeColor, zorder=3)
        ax.text(x_center-x_margin, y_center-text_y_margin, f'{len(hcent)}', fontsize=20, fontproperties=prop, fontweight='bold', color=pitch_color, ha='center', va='center')
        
        ax.scatter(x_center-x_margin, top_y, s=750, marker='o', color=homeColor, zorder=3)
        ax.text(x_center-x_margin, top_y-text_y_margin, f'{len(hrigt)}', fontsize=20, fontproperties=prop, fontweight='bold', color=pitch_color, ha='center', va='center')


        ax.scatter(x_center+x_margin, bottom_y, s=750, marker='o', color=awayColor, zorder=3)
        ax.text(x_center+x_margin, bottom_y-text_y_margin, f'{len(aleft)}', fontsize=20, fontproperties=prop, fontweight='bold', color=pitch_color, ha='center', va='center')
        
        ax.scatter(x_center+x_margin, y_center, s=750, marker='o', color=awayColor, zorder=3)
        ax.text(x_center+x_margin, y_center-text_y_margin, f'{len(acent)}', fontsize=20, fontproperties=prop, fontweight='bold', color=pitch_color, ha='center', va='center')
        
        ax.scatter(x_center+x_margin, top_y, s=750, marker='o', color=awayColor, zorder=3)
        ax.text(x_center+x_margin, top_y-text_y_margin, f'{len(arigt)}', fontsize=20, fontproperties=prop, fontweight='bold', color=pitch_color, ha='center', va='center')
        
        hometeamurl = f"https://images.fotmob.com/image_resources/logo/teamlogo/{homeTeamId}.png"
        awayteamurl = f"https://images.fotmob.com/image_resources/logo/teamlogo/{awayTeamId}.png"
        
        hometeam_logo = Image.open(BytesIO(requests.get(hometeamurl).content)).convert("RGBA")
        awayteam_logo = Image.open(BytesIO(requests.get(awayteamurl).content)).convert("RGBA")
        
        # Görseli küçültmek için OffsetImage kullanıyoruz
        home_imagebox = OffsetImage(hometeam_logo, zoom=0.1, alpha=0.5) 
        away_imagebox = OffsetImage(awayteam_logo, zoom=0.1, alpha=0.5) 

        # Görseli ortalamak için bir koordinat belirliyoruz
        x_center = (ax.get_xlim()[0] + ax.get_xlim()[1]) / 2

        # Görseli bu koordinata yerleştiriyoruz
        home = AnnotationBbox(home_imagebox, (x_center/8, 5), frameon=False)
        away = AnnotationBbox(away_imagebox, (x_center*1.875, 5), frameon=False)

        # Görseli eksene ekliyoruz
        ax.add_artist(home)
        ax.add_artist(away)
        
        pitch.lines(x_center/8+4, 5, x_center/8+16, 5, lw=3.5, transparent=True, comet=True, color=homeColor, ax=ax)
        pitch.scatter(x_center/8+16, 5, s=35, edgecolor=homeColor, linewidth=1, color=pitch_color, zorder=2, ax=ax)
        
        ax.text(x_center/8+18, 4.75, 'Pas İle', size=8, style='italic', ha="left", va="center", fontproperties=prop, color=homeColor)
        
        arrow_away = FancyArrowPatch((x_center*1.875-16, 5), (x_center*1.875-4, 5), color=awayColor, linewidth=1,  linestyle='--', arrowstyle='<-', mutation_scale=12, alpha=0.5)
        ax.add_patch(arrow_away)
        
        ax.text(x_center*1.875-16, 5, 'Top Sürme İle', size=8, style='italic', ha="right", va="center", fontproperties=prop, color=awayColor)
        
        ax.set_title(f"Ceza Sahasına Girişler", color=line_color, fontproperties=bold_prop, fontweight='bold', y=1.05)
        
        return

    def get_defensive_action_df(events_dict):
        # filter only defensive actions
        defensive_actions_ids = df.index[(df['type'] == 'Aerial') & (df['qualifiers'].str.contains('Defensive')) |
                                        (df['type'] == 'BallRecovery') |
                                        (df['type'] == 'BlockedPass') |
                                        (df['type'] == 'Challenge') |
                                        (df['type'] == 'Clearance') |
                                        (df['type'] == 'Error') |
                                        (df['type'] == 'Foul') |
                                        (df['type'] == 'Interception') |
                                        (df['type'] == 'Tackle')]
        df_defensive_actions = df.loc[defensive_actions_ids, ["index", "x", "y", "teamName", "playerId", "type", "outcomeType"]]
        
        return df_defensive_actions

    defensive_actions_df = get_defensive_action_df(events_dict)

    def get_da_count_df(team_name, defensive_actions_df, players_df):
        defensive_actions_df = defensive_actions_df[defensive_actions_df["teamName"] == team_name]
        # add column with first eleven players only
        defensive_actions_df = defensive_actions_df.merge(players_df[["playerId", "isFirstEleven"]], on='playerId', how='left')
        # calculate mean positions for players
        average_locs_and_count_df = (defensive_actions_df.groupby('playerId').agg({'x': ['median'], 'y': ['median', 'count']}))
        average_locs_and_count_df.columns = ['x', 'y', 'count']
        average_locs_and_count_df = average_locs_and_count_df.merge(players_df[['playerId', 'name', 'shirtNo', 'position', 'isFirstEleven']], on='playerId', how='left')
        average_locs_and_count_df = average_locs_and_count_df.set_index('playerId')

        return  average_locs_and_count_df

    defensive_home_average_locs_and_count_df = get_da_count_df(home_team_name, defensive_actions_df, players_df)
    defensive_away_average_locs_and_count_df = get_da_count_df(away_team_name, defensive_actions_df, players_df)
    defensive_home_average_locs_and_count_df = defensive_home_average_locs_and_count_df[defensive_home_average_locs_and_count_df['position'] != 'GK']
    defensive_away_average_locs_and_count_df = defensive_away_average_locs_and_count_df[defensive_away_average_locs_and_count_df['position'] != 'GK']

    def defensive_block(ax, average_locs_and_count_df, team_name, col):
        defensive_actions_team_df = defensive_actions_df[defensive_actions_df["teamName"] == team_name]
        pitch = Pitch(pitch_type='uefa', pitch_color=pitch_color, line_color=line_color, linewidth=2, line_zorder=2, corner_arcs=True, goal_type="line")
        pitch.draw(ax=ax)
        ax.set_facecolor(pitch_color)
        ax.set_xlim(-0.5, 105.5)
        ax.set_ylim(-0.5, 68.5)

        # using variable marker size for each player according to their defensive engagements
        MAX_MARKER_SIZE = 3500
        average_locs_and_count_df['marker_size'] = (average_locs_and_count_df['count']/ average_locs_and_count_df['count'].max() * MAX_MARKER_SIZE)
        # plotting the heatmap of the team defensive actions
        color = np.array(to_rgba(col))
        flamingo_cmap = LinearSegmentedColormap.from_list("Flamingo - 100 colors", [pitch_color, col], N=500)
        kde = pitch.kdeplot(defensive_actions_team_df.x, defensive_actions_team_df.y, ax=ax, fill=True, levels=5000, thresh=0.02, cut=4, cmap=flamingo_cmap)

        # using different node marker for starting and substitute players
        average_locs_and_count_df = average_locs_and_count_df[average_locs_and_count_df['isFirstEleven'] == True].reset_index(drop=True)
        for index, row in average_locs_and_count_df.iterrows():
            if row['isFirstEleven'] == True:
                da_nodes = pitch.scatter(row['x'], row['y'], s=row['marker_size']*1.2, marker='o', color=pitch_color, edgecolor=line_color, linewidth=1, 
                                    alpha=0.5, zorder=3, ax=ax)
        # plotting very tiny scatterings for the defensive actions
        da_scatter = pitch.scatter(defensive_actions_team_df.x, defensive_actions_team_df.y, s=10, marker='x', color='yellow', alpha=0.2, ax=ax)

        # Plotting the shirt no. of each player
        for index, row in average_locs_and_count_df.iterrows():
            player_initials = row["shirtNo"]
            pitch.annotate(player_initials, xy=(row.x, row.y), c=line_color, ha='center', va='center', size=(14), fontproperties=bold_prop, fontweight='bold', ax=ax)

        # Plotting a vertical line to show the median vertical position of all defensive actions, which is called Defensive Actions Height
        dah = round(average_locs_and_count_df['x'].mean(), 2)
        dah_show = round((dah*1.05), 2)
        ax.axvline(x=dah, color='gray', linestyle='--', alpha=0.75, linewidth=2)

        # Defense line Defensive Actions Height
        center_backs_height = average_locs_and_count_df[average_locs_and_count_df['position']=='DC']
        def_line_h = round(center_backs_height['x'].median(), 2)
        ax.axvline(x=def_line_h, color='gray', linestyle='dotted', alpha=0.5, linewidth=2)
        # Forward line Defensive Actions Height
        Forwards_height = average_locs_and_count_df[average_locs_and_count_df['isFirstEleven']==1]
        Forwards_height = Forwards_height.sort_values(by='x', ascending=False)
        Forwards_height = Forwards_height.head(2)
        fwd_line_h = round(Forwards_height['x'].mean(), 2)
        ax.axvline(x=fwd_line_h, color='gray', linestyle='dotted', alpha=0.5, linewidth=2)

        # Getting the compactness value 
        compactness = round((1 - ((fwd_line_h - def_line_h) / 105)) * 100, 2)

        # Headings and other texts
        if team_name == away_team_name:
            # inverting the axis for away team
            ax.invert_xaxis()
            ax.invert_yaxis()
            ax.text(dah-1, 73, f"{dah_show}m", fontsize=12, fontproperties=prop, color=line_color, ha='left', va='center')
        else:
            ax.text(dah-1, -5, f"{dah_show}m", fontsize=12, fontproperties=prop, color=line_color, ha='right', va='center')
            
        endnote = "Veri: WhoScored & FotMob\n@adnaaan433 projesinden ilham alındı"

        # Headlines and other texts
        if team_name == home_team_name:
            ax.text(105, -5, f'Kompaktlık:%{compactness}', fontsize=12, fontproperties=prop, color=line_color, ha='right', va='center')
            ax.set_title(f"{home_team_name} Defansif Aksiyonlar", fontproperties=bold_prop, color=line_color, fontweight='bold', y=1.05)
        else:
            ax.text(105, 73, f'Kompaktlık:%{compactness}', fontsize=12, fontproperties=prop, color=line_color, ha='left', va='center')
            ax.set_title(f"{away_team_name} Defansif Aksiyonlar", fontproperties=bold_prop, color=line_color, fontweight='bold', y=1.05)
            ax.text(0, 84, endnote, fontsize=12, fontproperties=prop, color=second_line_color, ha='right', style='italic', va='center')

        return

    def plot_congestion(ax):
        pitch = Pitch(pitch_type='uefa', pitch_color=pitch_color, line_color=line_color, goal_type="line", corner_arcs=True, line_zorder=6)
        pitch.draw(ax=ax)
        ax.set_xlim(-0.5,105.5)
        ax.set_ylim(-0.5,68.5)
        plt.axis('off')
        
        # Comparing open play touches of both teams in each zones of the pitch, if more than 55% touches for a team it will be coloured of that team, otherwise gray to represent contested
        pcmap = LinearSegmentedColormap.from_list("Pearl Earring - 10 colors",  [awayColor, dominate_pitch_color, homeColor], N=20)
        df1 = df[(df['teamName']==home_team_name) & (df['isTouch']==1) & (~df['qualifiers'].str.contains('CornerTaken|Freekick|ThrowIn'))].copy()
        df2 = df[(df['teamName']==away_team_name) & (df['isTouch']==1) & (~df['qualifiers'].str.contains('CornerTaken|Freekick|ThrowIn'))].copy()
        df2['x'] = 105-df2['x']
        df2['y'] =  68-df2['y']

        bin_statistic1 = pitch.bin_statistic(df1.x, df1.y, bins=(6,5), statistic='count', normalize=False)
        bin_statistic2 = pitch.bin_statistic(df2.x, df2.y, bins=(6,5), statistic='count', normalize=False)

        # Assuming 'cx' and 'cy' are as follows:
        cx = np.array([[ 8.75, 26.25, 43.75, 61.25, 78.75, 96.25],
                [ 8.75, 26.25, 43.75, 61.25, 78.75, 96.25],
                [ 8.75, 26.25, 43.75, 61.25, 78.75, 96.25],
                [ 8.75, 26.25, 43.75, 61.25, 78.75, 96.25],
                [ 8.75, 26.25, 43.75, 61.25, 78.75, 96.25]])

        cy = np.array([[61.2, 61.2, 61.2, 61.2, 61.2, 61.2],
                [47.6, 47.6, 47.6, 47.6, 47.6, 47.6],
                [34.0, 34.0, 34.0, 34.0, 34.0, 34.0],
                [20.4, 20.4, 20.4, 20.4, 20.4, 20.4],
                [ 6.8,  6.8,  6.8,  6.8,  6.8,  6.8]])

        # Flatten the arrays
        cx_flat = cx.flatten()
        cy_flat = cy.flatten()

        # Create a DataFrame
        df_cong = pd.DataFrame({'cx': cx_flat, 'cy': cy_flat})

        hd_values = []
        # Loop through the 2D arrays
        for i in range(bin_statistic1['statistic'].shape[0]):
            for j in range(bin_statistic1['statistic'].shape[1]):
                stat1 = bin_statistic1['statistic'][i, j]
                stat2 = bin_statistic2['statistic'][i, j]
            
                if (stat1 / (stat1 + stat2)) > 0.55:
                    hd_values.append(1)
                elif (stat1 / (stat1 + stat2)) < 0.45:
                    hd_values.append(0)
                else:
                    hd_values.append(0.5)

        df_cong['hd']=hd_values
        bin_stat = pitch.bin_statistic(df_cong.cx, df_cong.cy, bins=(6,5), values=df_cong['hd'], statistic='sum', normalize=False)
        pitch.heatmap(bin_stat, ax=ax, cmap=pcmap, edgecolors='#000000', lw=0, zorder=3, alpha=0.85)

        ax.set_title("Bölge Hakimiyetleri", color=line_color, fontweight='bold', fontproperties=bold_prop, y=1.05)

        ax.vlines(1*(105/6), ymin=0, ymax=68, color=pitch_color, lw=2, ls='--', zorder=10)
        ax.vlines(2*(105/6), ymin=0, ymax=68, color=pitch_color, lw=2, ls='--', zorder=10)
        ax.vlines(3*(105/6), ymin=0, ymax=68, color=pitch_color, lw=2, ls='--', zorder=10)
        ax.vlines(4*(105/6), ymin=0, ymax=68, color=pitch_color, lw=2, ls='--', zorder=10)
        ax.vlines(5*(105/6), ymin=0, ymax=68, color=pitch_color, lw=2, ls='--', zorder=10)

        ax.hlines(1*(68/5), xmin=0, xmax=105, color=pitch_color, lw=2, ls='--', zorder=10)
        ax.hlines(2*(68/5), xmin=0, xmax=105, color=pitch_color, lw=2, ls='--', zorder=10)
        ax.hlines(3*(68/5), xmin=0, xmax=105, color=pitch_color, lw=2, ls='--', zorder=10)
        ax.hlines(4*(68/5), xmin=0, xmax=105, color=pitch_color, lw=2, ls='--', zorder=10)
        
        return

    def generate_and_save_figure():
        # Daha büyük bir figür boyutu ve yüksek çözünürlük ayarları
        fig, axs = plt.subplots(4, 3, figsize=(20, 22), facecolor=pitch_color, edgecolor=line_color)
        
        # Grafiklerin her biri için uygun boyut ve font ayarları
        match_details(axs[0, 0])
        shotmap(axs[0, 1])
        momentum(axs[0, 2])
        pass_network_stats_home = pass_network_visualization(axs[1,0], home_passes_between_df, home_average_locs_and_count_df, homeColor, home_team_name)
        key_passes(axs[1, 1])
        pass_network_stats_away = pass_network_visualization(axs[1,2], away_passes_between_df, away_average_locs_and_count_df, awayColor, away_team_name)
        zone14_halfspace_home = zone14andhalfspace(axs[2, 0], home_team_name)
        box_entry(axs[2, 1])
        zone14_halfspace_away = zone14andhalfspace(axs[2, 2], away_team_name)
        defensive_block_stats_home = defensive_block(axs[3,0], defensive_home_average_locs_and_count_df, home_team_name, homeColor)
        plot_congestion(axs[3,1])
        defensive_block_stats_away = defensive_block(axs[3,2], defensive_away_average_locs_and_count_df, away_team_name, awayColor)
        
        # Yazı boyutları için genel ayarlar
        for ax in axs.flat:
            ax.title.set_fontsize(18)  # Başlık yazı boyutu
            ax.xaxis.label.set_fontsize(14)  # X ekseni etiket yazı boyutu
            ax.yaxis.label.set_fontsize(14)  # Y ekseni etiket yazı boyutu
            ax.tick_params(axis='both', which='major', labelsize=16)  # Tick etiket yazı boyutu
                    
        # Add text and images to the figure
        fig.text(0.2, 0.94, result_string, fontsize=34, fontweight='bold', ha='left', va='center', fontproperties=bold_prop, color=line_color)
        fig.text(0.2, 0.9175, matchDetailString, fontsize=20, ha='left', va='center', fontproperties=prop, color=line_color)
        
        # Yuvarlak köşeli dikdörtgen (FancyBboxPatch)
        fancy_rect = FancyBboxPatch((0.79, 0.93), 0.0833, 0.0001, boxstyle="round,pad=0.015,rounding_size=0.005", 
                                    transform=fig.transFigure, linewidth=2, edgecolor='black', facecolor=pitch_color, alpha=0.25)
        fig.patches.append(fancy_rect)  # fig.patches ile ekliyoruz
            
        # Gölge (arka katman)
        fig.text(0.886, 0.9285, "@bariscanyeksin", fontsize=18, ha='right', va='center', fontproperties=prop, color='gray', alpha=0.5)
        # Asıl yazı (ön katman)
        fig.text(0.885, 0.93, "@bariscanyeksin", fontsize=18, ha='right', va='center', fontproperties=prop, color=to_rgba(line_color, alpha=0.9))
        
        # 0.901, 0.9435 gölge
        # 0.9, 0.945 Asıl yazı
        
        league_logo_url = f"https://images.fotmob.com/image_resources/logo/leaguelogo/{fotmob_league_id}.png"
        league_logo = Image.open(BytesIO(requests.get(league_logo_url).content)).convert("RGBA")

        add_image(league_logo, fig, left=0.128, bottom=0.88, width=0.065, height=0.10)
        
        return fig

    final_fig = generate_and_save_figure()
    

    return final_fig
