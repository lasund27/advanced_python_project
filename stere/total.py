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
# 2. API Key Load (secrets.toml)
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
    st.session_state.current_view = "소환사 분석 (OP.GG)" # 기본값 변경

# -------------------------------------------------
# 4. CSS Styling
# -------------------------------------------------
st.markdown("""
<style>
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

/* 홈 버튼 (초기화) */
div.stButton > button.home-btn {
    background-color: #c8aa6e; color: #010a13; border: none; font-weight: bold;
}

/* 텍스트 인풋 */
div[data-testid="stTextInput"] input {
    background-color: #1e2328; color: #f0e6d2; border: 1px solid #3c3c44;
}

/* 카드 UI */
.challenge-card-inner {
    background-color: #1e2328; border: 2px solid #3c3c44; border-radius: 6px;
    padding: 15px; text-align: center; height: 100%; position: relative;
}
.champ-img { width: 45px; height: 45px; border-radius: 50%; border: 2px solid #c8aa6e; }
.bar-bg { width: 100%; height: 8px; background: #0a0a0c; border-radius: 4px; overflow: hidden; }
.bar-win { height: 100%; background: linear-gradient(90deg, #0ac8b9, #0a96a0); }

.landing-title { font-size: 60px; font-weight: 800; text-align: center; color: #00bba3; margin-bottom: 10px; }
.landing-subtitle { font-size: 18px; text-align: center; color: #a09b8c; margin-bottom: 30px; }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# 5. Sidebar (메뉴 항상 표시 / 메시지 제거)
# -------------------------------------------------
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/LoL_Icon_Flat_GOLD.svg/1200px-LoL_Icon_Flat_GOLD.svg.png", width=60)
    
    # 1. 홈으로 이동 버튼 (검색 상태일 때만 최상단 표시)
    if st.session_state.riot_id:
        if st.button("🏠 홈으로 (검색 초기화)", use_container_width=True):
            st.session_state.riot_id = ""
            st.rerun()
        st.markdown("---")
    
    # 2. 메뉴 (항상 표시)
    menu_options = ["소환사 분석 (OP.GG)", "도전과제 (API)"]
    selected_menu = st.radio("기능 선택", menu_options, 
                             index=menu_options.index(st.session_state.current_view))
    
    if selected_menu != st.session_state.current_view:
        st.session_state.current_view = selected_menu
        st.rerun()
    
    # 3. 불필요한 메시지 창 / ID 표시 제거됨

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
    fig = go.Figure(data=[go.Pie(labels=['A','B'], values=[per, 100-per], hole=0.75, marker=dict(colors=[color, 'rgba(255,255,255,0.1)']), textinfo='none', hoverinfo='none', sort=False)])
    fig.update_layout(annotations=[dict(text=f"{val:,}", x=0.5, y=0.55, font_size=24, font_color="#fff", showarrow=False, font_weight="bold"), dict(text=tier, x=0.5, y=0.35, font_size=14, font_color=color, showarrow=False)], margin=dict(l=0,r=0,t=0,b=0), height=160, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
    return fig

# -------------------------------------------------
# 7. Main Logic (View Routing)
# -------------------------------------------------

# [VIEW A] 소환사 분석 (OP.GG)
if st.session_state.current_view == "소환사 분석 (OP.GG)":
    # 1. ID가 없을 때 -> 랜딩 페이지 (검색창)
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

    # 2. ID가 있을 때 -> 대시보드
    else:
        name, tag = st.session_state.riot_id.split("#")
        st.markdown(f"## 📊 {name} <span style='color:#888;'>#{tag}</span>", unsafe_allow_html=True)
        st.divider()

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
                            <div class="bar-bg" style="width:80px;"><div class="bar-win" style="width:{rate}%"></div></div>
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
    # 1. ID가 없을 때 -> 검색창 표시
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
                    st.rerun()
                elif api_search:
                    st.toast("⚠️ 올바른 형식이 아닙니다.")
    
    # 2. ID가 있을 때 -> 대시보드
    else:
        name, tag = st.session_state.riot_id.split("#")
        with st.spinner("라이엇 API 조회 중..."):
            data, conf = get_player_data_api(name, tag)
            
        if data and conf:
            total = data.get('totalPoints', {})
            cur, maxx = total.get('current', 0), total.get('max', 1)
            
            c1, c2 = st.columns([1, 3])
            with c1: st.plotly_chart(make_donut(cur, maxx, total.get('level', 'IRON')), use_container_width=True, config={'displayModeBar':False})
            with c2:
                st.markdown(f"### {st.session_state.riot_id}")
                st.progress(min(cur/maxx, 1.0))
                st.caption(f"점수: {cur:,} / {maxx:,}")
            
            st.divider()
            
            challenges = [c for c in data.get('challenges', []) if c['challengeId'] > 10]
            sc1, sc2 = st.columns([3, 1])
            search_q = sc1.text_input("검색", placeholder="도전과제 이름...")
            sort_opt = sc2.selectbox("정렬", ["점수순", "티어순"])
            
            filtered = []
            for c in challenges:
                cfg = conf.get(str(c['challengeId']), {})
                loc = cfg.get('localizedNames', {}).get('ko_KR', {})
                name_txt = loc.get('name', 'Unknown')
                desc_txt = loc.get('description', '')
                if search_q and (search_q not in name_txt and search_q not in desc_txt): continue
                c['name_txt'] = name_txt
                c['desc_txt'] = desc_txt
                filtered.append(c)
            
            tier_order = ['NONE', 'IRON', 'BRONZE', 'SILVER', 'GOLD', 'PLATINUM', 'DIAMOND', 'MASTER', 'GRANDMASTER', 'CHALLENGER']
            if sort_opt == "점수순": filtered.sort(key=lambda x: x['value'], reverse=True)
            else: filtered.sort(key=lambda x: tier_order.index(x.get('level', 'NONE')), reverse=True)
            
            cols = st.columns(4)
            for i, c in enumerate(filtered[:20]):
                level = c.get('level', 'NONE')
                color = get_tier_color(level)
                icon = f"https://raw.communitydragon.org/latest/game/assets/challenges/config/{c['challengeId']}/tokens/{level.lower()}.png"
                with cols[i%4]:
                    st.markdown(f"""
                    <div class="challenge-card-inner" style="border-bottom:4px solid {color}; margin-bottom:10px; height:260px;">
                        <img src="{icon}" width="60">
                        <div style="font-weight:bold; margin:10px 0; height:45px; overflow:hidden;">{c['name_txt']}</div>
                        <div style="font-size:0.8em; color:#aaa; height:40px; overflow:hidden;">{c['desc_txt']}</div>
                        <div style="color:{color}; font-weight:bold;">{c['value']:,}</div>
                        <div style="color:{color}; font-size:0.8em;">{level}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.error("데이터 로드 실패 (ID 오류 또는 API 키 확인)")