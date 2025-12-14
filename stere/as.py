import streamlit as st
import requests
import urllib.parse
import plotly.graph_objects as go
import math  # [추가됨] 페이지 계산용

# --- 페이지 설정 ---
st.set_page_config(page_title="롤 도전과제 검색기", page_icon="🏆", layout="wide")

# --- 커스텀 CSS (디자인 수정) ---
st.markdown("""
<style>
    /* 1. 전체 다크 테마 적용 */
    .stApp {
        background-color: #010a13;
        color: #c8aa6e;
    }
    
    /* 2. 상단 여백 확보 */
    .block-container {
        padding-top: 5rem !important; 
        padding-bottom: 5rem;
        max-width: 1400px;
    }

    /* 3. 사이드바 스타일 */
    [data-testid="stSidebar"] {
        background-color: #091428;
        border-right: 1px solid #1e282d;
    }
    [data-testid="stSidebar"] * {
        color: #cdbe91 !important;
    }

    /* 4. 도전과제 카드 디자인 */
    .challenge-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 15px;
        margin-top: 20px;
    }
    
    .challenge-card {
        background-color: #1e2328;
        border: 2px solid #3c3c44;
        border-radius: 6px;
        padding: 15px;
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        transition: transform 0.2s, border-color 0.2s;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
    }
    
    .challenge-card:hover {
        transform: translateY(-5px);
        border-color: #f0e6d2;
        box-shadow: 0 5px 15px rgba(200, 170, 110, 0.2);
    }

    /* 텍스트 스타일 */
    .card-title {
        color: #f0e6d2;
        font-weight: bold;
        margin: 10px 0 5px 0;
        font-size: 1.1em;
        line-height: 1.2;
    }
    .card-desc {
        color: #a09b8c;
        font-size: 0.8em;
        margin-bottom: 10px;
        min-height: 32px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .card-footer {
        margin-top: auto;
        font-size: 0.9em;
        font-weight: bold;
        text-transform: uppercase;
    }

    /* 진행바 */
    .p-bar-bg {
        width: 100%;
        background-color: #0a0a0c;
        height: 20px;
        border-radius: 10px;
        overflow: hidden;
        margin-top: 10px;
        border: 1px solid #444;
        position: relative;
    }
    .p-bar-fill {
        height: 100%;
        background: linear-gradient(90deg, #0ac8b9, #0a96a0);
    }
    .p-bar-text {
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        display: flex; align-items: center; justify-content: center;
        font-size: 12px; color: white; text-shadow: 1px 1px 2px black;
    }
    
    /* 버튼 스타일 커스텀 */
    div.stButton > button {
        background-color: #1e2328;
        color: #c8aa6e;
        border: 1px solid #c8aa6e;
    }
    div.stButton > button:hover {
        background-color: #c8aa6e;
        color: #010a13;
        border-color: #f0e6d2;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- API 키 설정 ---
if "API_KEY" in st.secrets:
    API_KEY = st.secrets["API_KEY"]
else:
    API_KEY = "" # 여기에 API 키 입력

if not API_KEY:
    st.warning("⚠️ 코드 내 `API_KEY` 변수에 라이엇 API 키를 입력해주세요.")
    st.stop()

REGION_ACCOUNT = "asia"
REGION_KR = "kr"
HEADERS = {
    "X-Riot-Token": API_KEY,
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
}

# --- Helper Functions ---
def get_tier_color(tier):
    colors = {
        'IRON': '#585c62', 'BRONZE': '#8c523a', 'SILVER': '#86939e',
        'GOLD': '#d4af37', 'PLATINUM': '#07c8b9', 'DIAMOND': '#6c88ba',
        'MASTER': '#d153f5', 'GRANDMASTER': '#f03a3a', 'CHALLENGER': '#4baeff'
    }
    return colors.get(tier, '#3c3c44')

# --- API Functions ---
@st.cache_data(ttl=3600)
def get_puuid(game_name, tag_line):
    url = f"https://{REGION_ACCOUNT}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{urllib.parse.quote(game_name)}/{urllib.parse.quote(tag_line)}"
    try:
        res = requests.get(url, headers=HEADERS)
        return res.json().get('puuid') if res.status_code == 200 else None
    except: return None

@st.cache_data(ttl=3600)
def get_player_data(puuid):
    url = f"https://{REGION_KR}.api.riotgames.com/lol/challenges/v1/player-data/{puuid}"
    try:
        res = requests.get(url, headers=HEADERS)
        return res.json() if res.status_code == 200 else None
    except: return None

@st.cache_data(ttl=86400)
def get_all_challenge_config():
    url = f"https://{REGION_KR}.api.riotgames.com/lol/challenges/v1/challenges/config"
    try:
        res = requests.get(url, headers=HEADERS)
        if res.status_code == 200:
            data = res.json()
            return {str(item['id']): item for item in data}
        return None
    except: return None

# --- UI 생성 함수 ---
def make_html_card(challenge, config):
    c_id = str(challenge.get('challengeId'))
    points = challenge.get('value', 0)
    level = challenge.get('level', 'NONE')
    
    c_name = f"Unknown ({c_id})"
    c_desc = ""
    if config:
        names = config.get('localizedNames', {})
        ko = names.get('ko_KR') or names.get('en_US') or {}
        c_name = ko.get('name', c_name)
        c_desc = ko.get('description', '')
    
    if not c_desc: c_desc = "상세 설명 없음"
    c_desc = c_desc.replace("<br>", " ")

    color = get_tier_color(level)
    icon_url = f"https://raw.communitydragon.org/latest/game/assets/challenges/config/{c_id}/tokens/{level.lower()}.png"

    html = f"""
    <div class="challenge-card" style="border-bottom: 4px solid {color};">
        <div style="color:{color}; font-weight:bold; font-size:0.9em; margin-bottom:10px;">{points:,.0f} Pts</div>
        <div style="width:80px; height:80px; border-radius:50%; overflow:hidden; margin-bottom:10px; background:#121212; display:flex; justify-content:center; align-items:center;">
             <img src="{icon_url}" style="width:100%; height:100%; object-fit:contain;" onerror="this.style.display='none';">
        </div>
        <div class="card-title">{c_name}</div>
        <div class="card-desc" title="{c_desc}">{c_desc}</div>
        <div class="card-footer" style="color:{color};">{level}</div>
    </div>
    """
    return html

def make_donut(val, max_val, tier):
    per = (val/max_val*100) if max_val>0 else 0
    color = get_tier_color(tier)
    
    fig = go.Figure(data=[go.Pie(
        labels=['A','B'], values=[per, 100-per], hole=0.75,
        marker=dict(colors=[color, 'rgba(255,255,255,0.1)']),
        textinfo='none', hoverinfo='none', sort=False
    )])
    fig.update_layout(
        annotations=[
            dict(text=f"{val:,}", x=0.5, y=0.55, font_size=24, font_color="#fff", showarrow=False, font_weight="bold"),
            dict(text=tier, x=0.5, y=0.35, font_size=14, font_color=color, showarrow=False)
        ],
        margin=dict(l=0,r=0,t=0,b=0), height=160,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False
    )
    return fig

# --- Main Logic ---
if 'config' not in st.session_state:
    st.session_state.config = get_all_challenge_config()

# [추가됨] 페이지 상태 초기화
if 'page_num' not in st.session_state:
    st.session_state.page_num = 1

with st.sidebar:
    st.image("https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-clash/global/default/assets/images/rewards-modal/crest-icon-2.png", width=50)
    st.title("LoL Challenges")
    
    riot_id = st.text_input("Riot ID (이름#태그)", value="hide on bush#KR1")
    if st.button("검색", type="primary", use_container_width=True):
        if "#" in riot_id:
            n, t = riot_id.split('#')
            with st.spinner("불러오는 중..."):
                pid = get_puuid(n, t)
                if pid:
                    st.session_state.data = get_player_data(pid)
                    st.session_state.page_num = 1 # 검색 시 페이지 초기화
                else:
                    st.error("사용자 없음")

if st.session_state.get('data') and st.session_state.get('config'):
    data = st.session_state.data
    conf = st.session_state.config
    
    total = data.get('totalPoints', {})
    cur = total.get('current', 0)
    maxx = total.get('max', 20000)
    tier = total.get('level', 'IRON')

    # 헤더 섹션
    c1, c2 = st.columns([1, 4])
    with c1:
        st.plotly_chart(make_donut(cur, maxx, tier), use_container_width=True, config={'displayModeBar':False})
    with c2:
        per = min((cur/maxx*100), 100)
        st.markdown(f"""
        <div style="padding: 20px;">
            <h1 style="margin:0; color:#f0e6d2; font-size:2.5em;">전체 진행도</h1>
            <p style="color:#a09b8c;">모든 도전과제의 합산 점수입니다.</p>
            <div class="p-bar-bg">
                <div class="p-bar-fill" style="width: {per}%;"></div>
                <div class="p-bar-text">{cur:,} / {maxx:,}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    
    # 데이터 처리 및 페이지네이션
    challenges = sorted(data.get('challenges', []), key=lambda x: x['value'], reverse=True)
    real_challenges = [c for c in challenges if c['challengeId'] > 10]
    
    # 페이지 설정
    ITEMS_PER_PAGE = 24
    total_items = len(real_challenges)
    total_pages = math.ceil(total_items / ITEMS_PER_PAGE)
    
    # 페이지네이션 컨트롤 바
    col_prev, col_info, col_next = st.columns([1, 2, 1])
    
    with col_prev:
        if st.button("◀ 이전 페이지", use_container_width=True):
            if st.session_state.page_num > 1:
                st.session_state.page_num -= 1
                st.rerun()

    with col_next:
        if st.button("다음 페이지 ▶", use_container_width=True):
            if st.session_state.page_num < total_pages:
                st.session_state.page_num += 1
                st.rerun()
                
    with col_info:
        st.markdown(f"<div style='text-align:center; padding-top:10px; font-weight:bold;'>Page {st.session_state.page_num} / {total_pages}</div>", unsafe_allow_html=True)

    # 슬라이싱 (현재 페이지에 맞는 데이터만 추출)
    start_idx = (st.session_state.page_num - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    current_page_data = real_challenges[start_idx:end_idx]
    
    # 카드 생성
    card_htmls = []
    for c in current_page_data:
        card_htmls.append(make_html_card(c, conf.get(str(c['challengeId']))))
    
    final_html = f"""
    <div class="challenge-grid">
        {''.join(card_htmls)}
    </div>
    """
    
    st.markdown(final_html, unsafe_allow_html=True)
    
    # 하단 여백 추가
    st.markdown("<br><br>", unsafe_allow_html=True)

else:
    if not st.session_state.get('data'):
        st.info("👈 사이드바에서 아이디를 입력하고 검색하세요.")