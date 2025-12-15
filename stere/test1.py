import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import re
import urllib.parse
import plotly.graph_objects as go
import math
import random
import time

# -------------------------------------------------
# 1. Page Config
# -------------------------------------------------
st.set_page_config(
    page_title="LOL 종합 분석기",
    page_icon="🎮",
    layout="wide"
)

# -------------------------------------------------
# 2. API Key Load
# -------------------------------------------------
try:
    if "API_KEY" in st.secrets:
        API_KEY = st.secrets["API_KEY"]
    else:
        API_KEY = ""
except FileNotFoundError:
    API_KEY = ""

# -------------------------------------------------
# 3. State Management
# -------------------------------------------------
if 'riot_id' not in st.session_state:
    st.session_state.riot_id = ""
if 'current_view' not in st.session_state:
    st.session_state.current_view = "소환사 분석 (OP.GG)"
if 'page_num' not in st.session_state:
    st.session_state.page_num = 1
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""
# [NEW] 승급 임박 리스트 고정을 위한 상태 변수
if 'imminent_cache' not in st.session_state:
    st.session_state.imminent_cache = []

# -------------------------------------------------
# 4. CSS Styling
# -------------------------------------------------
st.markdown("""
<style>
/* 상단 헤더(Deploy 라인) 배경색 변경 */
header[data-testid="stHeader"] {
    background-color: #010a13 !important;
}

/* 기본 테마 */
.stApp { background-color: #010a13; color: #c8aa6e; }
.block-container { max-width: 1400px; padding-top: 2rem; }

/* 사이드바 */
[data-testid="stSidebar"] { background-color: #091428; border-right: 1px solid #1e282d; }
[data-testid="stSidebar"] * { color: #cdbe91 !important; }

/* 라디오 버튼 (메뉴) */
div.row-widget.stRadio > div { flex-direction: column; gap: 10px; }
div.row-widget.stRadio > div[role="radiogroup"] > label {
    background-color: #1e2328; border: 1px solid #3c3c44; padding: 12px; 
    border-radius: 8px; cursor: pointer; text-align: center; width: 100%;
}
div.row-widget.stRadio > div[role="radiogroup"] > label:hover {
    background-color: #2a3038; border-color: #c8aa6e;
}

/* 텍스트 인풋 & 버튼 & 셀렉트박스 */
div[data-testid="stTextInput"] input { background-color: #1e2328; color: #f0e6d2; border: 1px solid #3c3c44; }
div.stButton > button { background-color: #1e2328; color: #c8aa6e; border: 1px solid #c8aa6e; width: 100%; }
div.stButton > button:hover { background-color: #c8aa6e; color: #010a13; border-color: #f0e6d2; }
div[data-testid="stSelectbox"] > div > div { background-color: #1e2328; color: #f0e6d2; border: 1px solid #3c3c44; }

/* 카드 UI */
.challenge-card-inner {
    background-color: #1e2328; border: 2px solid #3c3c44; border-radius: 6px;
    padding: 10px; text-align: center; height: 280px; position: relative;
    display: flex; flex-direction: column; align-items: center; justify-content: flex-start;
}
.champ-img { width: 45px; height: 45px; border-radius: 50%; border: 2px solid #c8aa6e; }
.bar-bg { width: 100%; height: 8px; background: #0a0a0c; border-radius: 4px; overflow: hidden; }
.bar-win { height: 100%; background: linear-gradient(90deg, #0ac8b9, #0a96a0); }

/* 승급 임박 카드 */
.imminent-card {
    border: 2px solid #d13639 !important; background-color: #2a1e1e !important;
    box-shadow: 0 0 10px rgba(209, 54, 57, 0.2);
}
.imminent-badge {
    background-color: #d13639; color: white; padding: 2px 8px; border-radius: 4px;
    font-size: 0.8em; font-weight: bold; margin-bottom: 5px;
}

/* 랜덤 뽑기 카드 */
.spinning-card {
    border: 2px solid #c8aa6e !important; box-shadow: 0 0 20px rgba(200, 170, 110, 0.3);
    width: 300px; height: 350px; margin: 0 auto;
}

.landing-title { font-size: 60px; font-weight: 800; text-align: center; color: #00bba3; margin-bottom: 10px; }
.landing-subtitle { font-size: 18px; text-align: center; color: #a09b8c; margin-bottom: 30px; }

/* 프로그레스 바 스타일 (그라데이션) - 모달용 */
.progress-container {
    width: 100%;
    background-color: #eee;
    border-radius: 10px;
    height: 10px;
    margin-top: 5px;
    margin-bottom: 5px;
    overflow: hidden;
}
.progress-bar-gradient {
    height: 100%;
    border-radius: 10px;
    background: linear-gradient(90deg, #ff3b3b, #a020f0, #0099ff);
    transition: width 0.5s ease-in-out;
}

/* 인게임 정보 스타일 */
.ingame-box {
    background-color: #1a1a1a;
    border: 1px solid #3c3c44;
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 20px;
}
.team-header-blue { color: #4baeff; font-weight: bold; margin-bottom: 10px; border-bottom: 2px solid #4baeff; padding-bottom: 5px; }
.team-header-red { color: #f03a3a; font-weight: bold; margin-bottom: 10px; border-bottom: 2px solid #f03a3a; padding-bottom: 5px; }
.ingame-player-row {
    display: flex;
    align-items: center;
    margin-bottom: 8px;
    padding: 5px;
    border-radius: 5px;
    background-color: #1e2328;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# 5. Sidebar
# -------------------------------------------------
with st.sidebar:
    if st.session_state.riot_id:
        if st.button("🏠 홈으로 (검색 초기화)", use_container_width=True):
            st.session_state.riot_id = ""
            st.session_state.page_num = 1
            st.session_state.imminent_cache = []
            st.rerun()
        st.markdown("---")
    
    menu_options = ["소환사 분석 (OP.GG)", "도전과제 (API)"]
    selected_menu = st.radio("기능 선택", menu_options, 
                             index=menu_options.index(st.session_state.current_view))
    
    if selected_menu != st.session_state.current_view:
        st.session_state.current_view = selected_menu
        st.rerun()

# -------------------------------------------------
# 6. Helper Functions
# -------------------------------------------------
def get_tier_color(tier):
    colors = {'IRON': '#585c62', 'BRONZE': '#8c523a', 'SILVER': '#86939e', 'GOLD': '#d4af37', 'PLATINUM': '#07c8b9', 'DIAMOND': '#6c88ba', 'MASTER': '#d153f5', 'GRANDMASTER': '#f03a3a', 'CHALLENGER': '#4baeff'}
    return colors.get(tier, '#3c3c44')

HEADERS_SCRAP = {"User-Agent": "Mozilla/5.0"}
@st.cache_data(ttl=600)
def fetch_opgg_data(name, tag):
    encoded = f"{quote(name)}-{quote(tag)}"
    try:
        r_champ = requests.get(f"https://op.gg/ko/lol/summoners/kr/{encoded}/champions", headers=HEADERS_SCRAP)
        r_mastery = requests.get(f"https://op.gg/ko/lol/summoners/kr/{encoded}/mastery", headers=HEADERS_SCRAP)
        return r_champ.text, r_mastery.text
    except: return None, None

def parse_champs(html):
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    result = []
    for r in soup.select("tbody tr"):
        try:
            txt = r.get_text(" ", strip=True).lower()
            if "vs" in txt: continue
            img = r.find("img")
            if not img: continue
            w = re.search(r"(\d+)\s*승", txt)
            l = re.search(r"(\d+)\s*패", txt)
            wins = int(w.group(1)) if w else 0
            losses = int(l.group(1)) if l else 0
            if wins+losses == 0: continue
            result.append({"name": img["alt"], "img": img["src"], "wins": wins, "losses": losses})
            if len(result) == 9: break
        except: continue
    return result

def parse_mastery(html):
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select("div[data-tooltip-id^='opgg-tooltip']") or soup.select("li > div > img")
    result = []
    for item in items[:6]:
        try:
            img = item.find("img") if item.name != 'img' else item
            score_span = item.find_next("span", string=re.compile(r"[\d,]+"))
            if not img: continue
            score = score_span.text.strip() if score_span else "N/A"
            result.append({"name": img.get("alt",""), "img": img.get("src",""), "score": score})
        except: continue
    return result

HEADERS_API = {"X-Riot-Token": API_KEY, "User-Agent": "Mozilla/5.0"}

# [NEW] DDragon 챔피언 정보 가져오기 (ID -> 이름/이미지 매핑용)
@st.cache_data(ttl=86400)
def get_champion_map():
    try:
        ver_res = requests.get("https://ddragon.leagueoflegends.com/api/versions.json")
        version = ver_res.json()[0]
        res = requests.get(f"https://ddragon.leagueoflegends.com/cdn/{version}/data/ko_KR/champion.json")
        data = res.json()['data']
        # Key(ID) : {'name': 이름, 'id': 영문ID(이미지용)}
        return {v['key']: {'name': v['name'], 'id': v['id']} for k, v in data.items()}, version
    except: return {}, "latest"

# 소환사 정보(PUUID)만 가져오는 함수
@st.cache_data(ttl=3600)
def get_puuid_only(name, tag):
    try:
        acc_url = f"https://asia.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{quote(name)}/{quote(tag)}"
        acc_res = requests.get(acc_url, headers=HEADERS_API)
        if acc_res.status_code == 200:
            return acc_res.json().get('puuid')
        return None
    except: return None

# 인게임 정보 조회 함수
def get_active_game(puuid):
    try:
        url = f"https://kr.api.riotgames.com/lol/spectator/v5/active-games/by-summoner/{puuid}"
        res = requests.get(url, headers=HEADERS_API)
        if res.status_code == 200:
            return res.json()
        return None
    except: return None

@st.cache_data(ttl=3600)
def get_player_data_api(name, tag):
    try:
        acc_url = f"https://asia.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{quote(name)}/{quote(tag)}"
        acc_res = requests.get(acc_url, headers=HEADERS_API)
        if acc_res.status_code != 200: return None, None
        puuid = acc_res.json().get('puuid')
        
        chal_url = f"https://kr.api.riotgames.com/lol/challenges/v1/player-data/{puuid}"
        chal_res = requests.get(chal_url, headers=HEADERS_API)
        
        conf_url = f"https://kr.api.riotgames.com/lol/challenges/v1/challenges/config"
        conf_res = requests.get(conf_url, headers=HEADERS_API)
        
        if chal_res.status_code == 200 and conf_res.status_code == 200:
            config_map = {str(item['id']): item for item in conf_res.json()}
            return chal_res.json(), config_map
        return None, None
    except: return None, None

def make_donut(val, max_val, tier):
    per = (val/max_val*100) if max_val>0 else 0
    color = get_tier_color(tier)
    fig = go.Figure(data=[go.Pie(
        labels=['A','B'], 
        values=[per, 100-per], 
        hole=0.75, 
        marker=dict(colors=[color, 'rgba(255,255,255,0.1)']), 
        textinfo='none', 
        hoverinfo='none', 
        sort=False
    )])
    fig.update_layout(
        annotations=[
            dict(text=f"{val:,}", x=0.5, y=0.55, font_size=20, font_color="#fff", showarrow=False, font_weight="bold"), 
            dict(text=tier, x=0.5, y=0.35, font_size=12, font_color=color, showarrow=False)
        ], 
        margin=dict(l=0,r=0,t=0,b=0), 
        height=140, 
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)', 
        showlegend=False
    )
    return fig

def calculate_next_level(challenge_info, config_info):
    current_val = challenge_info.get('value', 0)
    current_level = challenge_info.get('level', 'NONE')
    thresholds = config_info.get('thresholds', {})
    order = ['IRON', 'BRONZE', 'SILVER', 'GOLD', 'PLATINUM', 'DIAMOND', 'MASTER', 'GRANDMASTER', 'CHALLENGER']
    
    prev_threshold = 0
    next_tier = "MAX"
    next_threshold = current_val

    try:
        curr_idx = order.index(current_level)
        if curr_idx < len(order) - 1:
            next_tier = order[curr_idx + 1]
            next_threshold = thresholds.get(next_tier, current_val)
            prev_threshold = thresholds.get(current_level, 0)
        else:
            next_tier = "MAX"
            next_threshold = current_val
            prev_threshold = thresholds.get('GRANDMASTER', 0)
    except ValueError:
        next_tier = 'IRON'
        next_threshold = thresholds.get('IRON', 0)
        prev_threshold = 0

    return next_tier, prev_threshold, next_threshold

@st.dialog("도전과제 상세 정보")
def show_detail_modal(c, cfg):
    level = c.get('level', 'NONE')
    
    color = get_tier_color(level)
    if level == 'GRANDMASTER': color = '#ff3b3b'
    if level == 'CHALLENGER': color = '#0099ff'

    icon = f"https://raw.communitydragon.org/latest/game/assets/challenges/config/{c['challengeId']}/tokens/{level.lower()}.png"
    
    c1, c2 = st.columns([1, 4], vertical_alignment="center")
    with c1: 
        st.image(icon, width=80)
    with c2:
        st.markdown(f"<h3 style='margin:0; padding:0; color:#f0e6d2;'>{c.get('name_txt', 'Unknown')}</h3>", unsafe_allow_html=True)
        st.markdown(f"<span style='color:{color}; font-weight:bold; font-size:1.3em;'>{level}</span>", unsafe_allow_html=True)
        if c.get('percentile', 0) > 0:
             st.markdown(f"<div style='font-size:0.8em; color:#888; margin-top: 2px;'>👥 플레이어 중 상위 {c.get('percentile', 0)*100:.1f}%가 획득</div>", unsafe_allow_html=True)
    
    st.markdown("<hr style='margin: 15px 0; border-color: #333;'>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="background-color: #e8f4fd; padding: 15px; border-radius: 6px; color: #202b3d; font-weight: 500; font-size: 0.95em; margin-bottom: 20px;">
        {c.get('desc_txt', '설명 없음')}
    </div>
    """, unsafe_allow_html=True)

    next_tier, prev_th, next_th = calculate_next_level(c, cfg)
    
    if next_tier != "MAX":
        range_val = next_th - prev_th
        current_progress = c.get('value', 0) - prev_th
        if range_val <= 0: range_val = 1 
        ratio = min(max(current_progress / range_val, 0.0), 1.0) 

        st.markdown(f"<div style='font-size:0.9em; margin-bottom:5px; color: #ccc;'>다음 단계: <span style='color:#0099ff; font-weight:bold;'>{next_tier}</span></div>", unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; font-size:0.8em; color:#888; margin-bottom:2px;">
            <span>{c.get('value', 0):,}</span>
            <span>{next_th:,}</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="progress-container">
            <div class="progress-bar-gradient" style="width:{ratio*100}%;"></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="text-align:right; font-size:0.8em; color:#aaa; margin-top:5px;">
            목표까지 {next_th - c.get('value', 0):,} 남음
        </div>
        """, unsafe_allow_html=True)
    else:
        st.success("최고 등급 달성!")
        st.metric(label="최종 점수", value=f"{c.get('value', 0):,} Pts")

# -------------------------------------------------
# 7. Main Logic
# -------------------------------------------------

# [VIEW A] 소환사 분석 (OP.GG)
if st.session_state.current_view == "소환사 분석 (OP.GG)":
    if not st.session_state.riot_id:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown('<div class="landing-title">LOL 분석기</div>', unsafe_allow_html=True)
        st.markdown('<div class="landing-subtitle">소환사 분석 (OP.GG)</div>', unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            home_search = st.text_input("소환사명 (닉네임#태그)", placeholder="ex) Hide on bush#KR1", key="search_opgg")
            if st.button("검색 시작", use_container_width=True):
                if home_search and "#" in home_search:
                    st.session_state.riot_id = home_search
                    st.rerun()
                elif home_search:
                    st.toast("⚠️ 올바른 형식이 아닙니다. (#태그 포함)")
    else:
        name, tag = st.session_state.riot_id.split("#")
        
        st.markdown(f"## {name} <span style='color:#888;'>#{tag}</span>", unsafe_allow_html=True)
        st.divider()

        # [NEW] 인게임 정보 조회 섹션
        with st.expander("📺 인게임 정보 (실시간 게임 확인)", expanded=False):
            if st.button("현재 게임 정보 불러오기", use_container_width=True):
                if not API_KEY:
                    st.error("API 키가 없습니다. 코드에 API 키를 입력해주세요.")
                else:
                    with st.spinner("게임 정보를 찾는 중..."):
                        puuid = get_puuid_only(name, tag)
                        if puuid:
                            game_data = get_active_game(puuid)
                            if game_data:
                                # 챔피언 정보 로드
                                champ_map, d_ver = get_champion_map()
                                
                                # 게임 정보 표시
                                team_blue = [] # Team ID 100
                                team_red = []  # Team ID 200
                                
                                for p in game_data.get('participants', []):
                                    p_riot_id = p.get('riotId', 'Unknown#KR1')
                                    c_id = str(p.get('championId'))
                                    c_info = champ_map.get(c_id, {'name': 'Unknown', 'id': None})
                                    
                                    # 챔피언 이미지 URL
                                    c_img_url = ""
                                    if c_info['id']:
                                        c_img_url = f"https://ddragon.leagueoflegends.com/cdn/{d_ver}/img/champion/{c_info['id']}.png"
                                    
                                    player_info = {
                                        'name': p_riot_id,
                                        'champ_name': c_info['name'],
                                        'img': c_img_url
                                    }

                                    if p.get('teamId') == 100:
                                        team_blue.append(player_info)
                                    else:
                                        team_red.append(player_info)
                                
                                st.markdown("<div class='ingame-box'>", unsafe_allow_html=True)
                                ig_c1, ig_c2 = st.columns(2)
                                
                                with ig_c1:
                                    st.markdown("<div class='team-header-blue'>🟦 블루팀 (Blue Team)</div>", unsafe_allow_html=True)
                                    for p in team_blue:
                                        c1_sub, c2_sub = st.columns([1, 4])
                                        with c1_sub:
                                            if p['img']: st.image(p['img'], width=40)
                                        with c2_sub:
                                            if st.button(f"{p['champ_name']} - {p['name']}", key=f"btn_b_{p['name']}", use_container_width=True):
                                                st.session_state.riot_id = p['name']
                                                st.rerun()
                                
                                with ig_c2:
                                    st.markdown("<div class='team-header-red'>🟥 레드팀 (Red Team)</div>", unsafe_allow_html=True)
                                    for p in team_red:
                                        c1_sub, c2_sub = st.columns([1, 4])
                                        with c1_sub:
                                            if p['img']: st.image(p['img'], width=40)
                                        with c2_sub:
                                            if st.button(f"{p['champ_name']} - {p['name']}", key=f"btn_r_{p['name']}", use_container_width=True):
                                                st.session_state.riot_id = p['name']
                                                st.rerun()
                                st.markdown("</div>", unsafe_allow_html=True)
                            else:
                                st.info("현재 게임 중이 아닙니다. (또는 API 키 권한 문제)")
                        else:
                            st.error("소환사 정보를 찾을 수 없습니다. (Riot ID 확인)")

        c_html, m_html = fetch_opgg_data(name, tag)
        if c_html:
            champs = parse_champs(c_html)
            mastery = parse_mastery(m_html)
            
            c1, c2 = st.columns([1.5, 1])
            with c1:
                st.subheader("모스트 픽 (최근)")
                if not champs: st.warning("최근 랭크 데이터가 없습니다.")
                for c in champs:
                    tot = c['wins'] + c['losses']
                    rate = int(c['wins']/tot*100)
                    st.markdown(f"""
                    <div style="display:flex; align-items:center; margin-bottom:8px;">
                        <img src="{c['img']}" class="champ-img" style="margin-right:15px;">
                        <div style="flex:1;">
                            <div style="font-weight:bold; color:#f0e6d2;">{c['name']}</div>
                            <div style="font-size:0.8em; color:#888;">{c['wins']}승 {c['losses']}패</div>
                        </div>
                        <div style="text-align:right;">
                            <div class="bar-bg" style="width:250px;"><div class="bar-win" style="width:{rate}%"></div></div>
                            <span class="win-text">{rate}%</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            with c2:
                st.subheader("숙련도")
                cols = st.columns(2)
                for i, m in enumerate(mastery):
                    with cols[i%2]:
                        st.markdown(f"""
                        <div style="background:#1e2328; padding:10px; border-radius:8px; text-align:center; margin-bottom:10px; border:1px solid #3c3c44;">
                            <img src="{m['img']}" width="50" style="border-radius:50%;">
                            <div style="font-size:0.9em; font-weight:bold; margin-top:5px;">{m['name']}</div>
                            <div style="color:#e2b714; font-size:0.8em;">{m['score']}</div>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.error("데이터를 불러오지 못했습니다.")

# [VIEW B] 도전과제 (API)
elif st.session_state.current_view == "도전과제 (API)":
    if not st.session_state.riot_id:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown('<div class="landing-title">도전과제 검색</div>', unsafe_allow_html=True)
        st.markdown('<div class="landing-subtitle">Riot API 기반 도전과제 조회</div>', unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            api_search = st.text_input("소환사명 (닉네임#태그)", placeholder="ex) Hide on bush#KR1", key="search_api")
            if st.button("조회 하기", use_container_width=True):
                if api_search and "#" in api_search:
                    st.session_state.riot_id = api_search
                    st.session_state.page_num = 1
                    st.session_state.imminent_cache = [] # 검색 시 캐시 초기화
                    st.rerun()
                elif api_search:
                    st.toast("⚠️ 올바른 형식이 아닙니다.")
    
    else:
        name, tag = st.session_state.riot_id.split("#")
        with st.spinner("라이엇 API 조회 중..."):
            data, conf = get_player_data_api(name, tag)
            
        if data and conf:
            # 상단 여백
            st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)

            # 1. 상단 정보
            total = data.get('totalPoints', {})
            cur, maxx = total.get('current', 0), total.get('max', 1)
            per = min((cur/maxx*100), 100)
            
            c1, c2 = st.columns([1, 4])
            with c1:
                st.plotly_chart(make_donut(cur, maxx, total.get('level', 'IRON')), use_container_width=True, config={'displayModeBar':False})
            with c2:
                st.markdown(f"""
                <div style="padding: 20px 0;">
                    <h1 style="margin:0; color:#c8aa6e; font-size:2em; margin-bottom: 10px;">{st.session_state.riot_id}</h1>
                    <div style="background-color:#1e2328; height:10px; border-radius:5px; position:relative; overflow:hidden;">
                        <div style="width:{per}%; background-color:#0099ff; height:100%; box-shadow: 0 0 10px #0099ff;"></div>
                    </div>
                    <div style="margin-top: 8px; color: #888; font-size: 0.9em;">
                        점수: {cur:,} / {maxx:,}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.divider()

            # 2. 데이터 전처리
            challenges = [c for c in data.get('challenges', []) if c['challengeId'] > 10]
            enriched_challenges = []
            
            for c in challenges:
                cfg = conf.get(str(c['challengeId']), {})
                loc = cfg.get('localizedNames', {}).get('ko_KR', {})
                c['name_txt'] = loc.get('name', 'Unknown')
                c['desc_txt'] = loc.get('description', '')
                enriched_challenges.append(c)

            # 3. 컨트롤 패널
            col_search, col_sort, col_rand = st.columns([2, 1, 1], vertical_alignment="bottom")
            with col_search:
                search_input = st.text_input("🔍 이름 검색", placeholder="도전과제명...", value=st.session_state.search_query, label_visibility="collapsed")
            with col_sort:
                sort_opt = st.selectbox("정렬 기준", ["점수 높은 순", "점수 낮은 순", "티어 높은 순", "티어 낮은 순"], label_visibility="collapsed")
            with col_rand:
                rand_btn = st.button("🎲 랜덤 뽑기", use_container_width=True)

            if search_input != st.session_state.search_query:
                st.session_state.search_query = search_input
                st.session_state.page_num = 1
                st.rerun()

            # 4. 필터링
            filtered = []
            for c in enriched_challenges:
                if st.session_state.search_query and (st.session_state.search_query not in c['name_txt'] and st.session_state.search_query not in c['desc_txt']):
                    continue
                filtered.append(c)

            tier_order = ['NONE', 'IRON', 'BRONZE', 'SILVER', 'GOLD', 'PLATINUM', 'DIAMOND', 'MASTER', 'GRANDMASTER', 'CHALLENGER']
            
            if sort_opt == "점수 높은 순": filtered.sort(key=lambda x: x['value'], reverse=True)
            elif sort_opt == "점수 낮은 순": filtered.sort(key=lambda x: x['value'])
            elif sort_opt == "티어 높은 순": filtered.sort(key=lambda x: tier_order.index(x.get('level', 'NONE')), reverse=True)
            elif sort_opt == "티어 낮은 순": filtered.sort(key=lambda x: tier_order.index(x.get('level', 'NONE')))

            items_per_page = 20
            total_pages = math.ceil(len(filtered) / items_per_page)
            if st.session_state.page_num > total_pages: st.session_state.page_num = 1

            st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
            
            col_prev, col_spacer, col_page, col_spacer, col_next, col_spacer, col_chk = st.columns([4, 1, 2, 1, 4, 1, 3], vertical_alignment="center")
            
            with col_prev:
                if st.button("◀ 이전", use_container_width=True, key="prev_btn") and st.session_state.page_num > 1:
                    st.session_state.page_num -= 1
                    st.rerun()
            with col_page:
                st.markdown(f"<div style='text-align:center; color:#a09b8c; white-space:nowrap;'>Page {st.session_state.page_num} / {total_pages} ({len(filtered)}개)</div>", unsafe_allow_html=True)
            with col_next:
                if st.button("다음 ▶", use_container_width=True, key="next_btn") and st.session_state.page_num < total_pages:
                    st.session_state.page_num += 1
                    st.rerun()
            with col_chk:
                sub_c1, sub_c2 = st.columns([3, 1], vertical_alignment="center")
                with sub_c1:
                    show_imminent = st.checkbox("🔥 승급 임박 보기", value=False)
                with sub_c2:
                    if show_imminent:
                        if st.button("🔄", help="목록 새로고침", use_container_width=True):
                            st.session_state.imminent_cache = []
                            st.rerun()

            # 5. 랜덤 뽑기
            if rand_btn:
                spin_placeholder = st.empty()
                if enriched_challenges:
                    total_frames = 30
                    for i in range(total_frames):
                        pick = random.choice(enriched_challenges)
                        level = pick.get('level', 'NONE')
                        icon = f"https://raw.communitydragon.org/latest/game/assets/challenges/config/{pick['challengeId']}/tokens/{level.lower()}.png"
                        
                        spin_placeholder.markdown(f"""
                        <div class="challenge-card-inner spinning-card">
                            <h3 style='color:#c8aa6e'>🎲 추첨 중...</h3>
                            <img src="{icon}" width="100" style="margin:20px 0;">
                            <div style="font-weight:bold; font-size:1.2em; color:#f0e6d2;">{pick['name_txt']}</div>
                            <div style="color:{get_tier_color(level)};">{level}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        sleep_time = 0.02 + (i / total_frames) ** 2 * 0.2
                        time.sleep(sleep_time)
                    
                    spin_placeholder.empty()
                    final_pick = random.choice(enriched_challenges)
                    show_detail_modal(final_pick, conf.get(str(final_pick['challengeId']), {}))

            # 6. 승급 임박 로직 (목록 고정)
            if show_imminent:
                limit_diff = 500

                if not st.session_state.imminent_cache:
                    temp_list = []
                    for c in enriched_challenges:
                        cfg = conf.get(str(c['challengeId']), {})
                        next_tier, _, next_th = calculate_next_level(c, cfg)
                        if next_tier != "MAX":
                            diff = next_th - c.get('value', 0)
                            if 0 < diff <= limit_diff:
                                temp_list.append({'c': c, 'diff': diff, 'next': next_tier, 'cfg': cfg})
                    
                    if temp_list:
                        random.shuffle(temp_list)
                        st.session_state.imminent_cache = temp_list[:4]
                    else:
                        st.session_state.imminent_cache = []

                top_imminent = st.session_state.imminent_cache

                if top_imminent:
                    st.markdown(f"##### 🔥 승급 임박! (기준: {limit_diff}점 이하, 랜덤 4개)")
                    i_cols = st.columns(4)
                    for i, item in enumerate(top_imminent):
                        c = item['c']
                        level = c.get('level', 'NONE')
                        icon = f"https://raw.communitydragon.org/latest/game/assets/challenges/config/{c['challengeId']}/tokens/{level.lower()}.png"
                        with i_cols[i]:
                            st.markdown(f"""
                            <div class="challenge-card-inner imminent-card" style="height:250px;">
                                <div class="imminent-badge">D-{item['diff']:,}</div>
                                <img src="{icon}" width="60" style="margin-bottom:10px;">
                                <div style="font-weight:bold; color:#f0e6d2; font-size:0.9em; height:40px; overflow:hidden;">{c['name_txt']}</div>
                                <div style="font-size:0.8em; color:#e0e0e0; height:40px; overflow:hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">{c['desc_txt']}</div>
                                <div style="font-size:0.8em; color:#aaa; margin-top:5px;">Next: <span style="color:{get_tier_color(item['next'])}">{item['next']}</span></div>
                            </div>
                            """, unsafe_allow_html=True)
                            if st.button("상세", key=f"imm_{c['challengeId']}", use_container_width=True):
                                show_detail_modal(c, item['cfg'])
                else:
                    st.info(f"💡 현재 설정된 기준({limit_diff}점) 이내의 승급 임박 과제가 없습니다.")
                    
                st.divider()

            # 7. 그리드 출력
            start_idx = (st.session_state.page_num - 1) * items_per_page
            end_idx = start_idx + items_per_page
            current_items = filtered[start_idx:end_idx]

            st.markdown("<br>", unsafe_allow_html=True)
            cols = st.columns(4)
            for i, c in enumerate(current_items):
                level = c.get('level', 'NONE')
                color = get_tier_color(level)
                icon = f"https://raw.communitydragon.org/latest/game/assets/challenges/config/{c['challengeId']}/tokens/{level.lower()}.png"
                
                with cols[i%4]:
                    st.markdown(f"""
                    <div class="challenge-card-inner" style="border-bottom:4px solid {color};">
                        <img src="{icon}" width="60">
                        <div style="font-weight:bold; margin:10px 0; height:45px; overflow:hidden; color:#f0e6d2;">{c['name_txt']}</div>
                        <div style="font-size:0.8em; color:#e0e0e0; height:40px; overflow:hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">{c['desc_txt']}</div>
                        <div style="margin-top:auto; width:100%;">
                            <div style="color:{color}; font-weight:bold;">{c['value']:,}</div>
                            <div style="color:{color}; font-size:0.8em;">{level}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("상세 정보", key=f"btn_{c['challengeId']}", use_container_width=True):
                        show_detail_modal(c, conf.get(str(c['challengeId']), {}))
            
            st.markdown("<br>", unsafe_allow_html=True)

        else:
            st.error("데이터 로드 실패 (ID 오류 또는 API 키 확인)")