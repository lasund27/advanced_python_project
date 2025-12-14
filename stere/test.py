import streamlit as st
import requests
import urllib.parse
import math

# --- 페이지 설정 ---
st.set_page_config(page_title="롤 도전과제 검색기", page_icon="🏆", layout="wide")

# --- 커스텀 CSS (깔끔한 LoL 스타일 적용) ---
st.markdown("""
<style>
    /* 1. 기본 테마 설정 */
    .stApp { background-color: #010a13; color: #c8aa6e; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    .block-container { max-width: 1200px; padding-top: 2rem; }
    [data-testid="stSidebar"] { background-color: #091428; border-right: 1px solid #1e282d; }
    
    /* 2. 카드 컨테이너 */
    .challenge-card-container {
        margin-bottom: 15px;
        border-radius: 4px;
        overflow: hidden;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }

    /* 3. 카드 헤더 (요약 정보 - 클릭 가능한 부분) */
    .card-header {
        background-color: #1e2328;
        border: 1px solid #3c3c44;
        padding: 12px 15px;
        display: flex;
        align-items: center;
        gap: 15px;
        transition: all 0.2s ease;
    }
    .card-header:hover {
        background-color: #252a33;
        border-color: #c8aa6e;
        cursor: pointer;
    }
    
    /* 4. 카드 바디 (상세 정보 - 펼쳐지는 부분) */
    .card-body {
        background-color: #121418;
        border: 1px solid #3c3c44;
        border-top: none;
        padding: 15px;
        animation: slideDown 0.3s ease-out;
    }
    @keyframes slideDown {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* 5. 롤 클라이언트 스타일 진행바 (핵심 디자인) */
    .lol-progress-frame {
        width: 100%;
        height: 24px;
        background-color: #050505; /* 아주 어두운 배경 */
        border: 1px solid #333;
        position: relative; /* 텍스트를 위에 띄우기 위함 */
        margin: 15px 0;
        border-radius: 2px;
    }
    
    .lol-progress-bar {
        height: 100%;
        /* 청록색 그라데이션 (스크린샷 참조) */
        background: linear-gradient(90deg, #005a82 0%, #0ac8b9 100%);
        box-shadow: inset 0 0 5px rgba(0,0,0,0.5);
        transition: width 0.5s ease-in-out;
    }
    
    .lol-progress-text {
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        display: flex; align-items: center; justify-content: center;
        color: #ffffff;
        font-weight: bold;
        font-size: 13px;
        text-shadow: 1px 1px 2px #000;
        letter-spacing: 0.5px;
        z-index: 10; /* 바보다 위에 표시 */
    }

    /* 6. 텍스트 및 기타 스타일 */
    .challenge-name { color: #f0e6d2; font-weight: 700; font-size: 1.1em; margin-bottom: 4px; }
    .tier-text { font-size: 0.85em; font-weight: 600; letter-spacing: 0.5px; }
    .points-text { font-size: 0.85em; color: #888; margin-top: 4px; }
    .desc-text { color: #a09b8c; font-size: 0.9em; line-height: 1.4; }
    .info-text { font-size: 0.8em; color: #666; }
    .friend-text { color: #888; font-size: 0.85em; display: flex; align-items: center; gap: 8px; }

    /* Streamlit 버튼 스타일 커스텀 (카드와 한 몸처럼 보이게) */
    div.stButton > button {
        width: 100%;
        background-color: #1e2328;
        color: #c8aa6e;
        border: 1px solid #3c3c44;
        border-top: none; /* 헤더와 연결된 느낌 */
        border-radius: 0 0 4px 4px;
        padding: 8px;
        font-size: 0.9em;
        transition: all 0.2s;
    }
    div.stButton > button:hover {
        background-color: #252a33;
        border-color: #c8aa6e;
        color: #f0e6d2;
    }
    
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- API 키 설정 ---
if "API_KEY" in st.secrets:
    API_KEY = st.secrets["API_KEY"]
else:
    # API 키를 여기에 직접 입력하거나, secrets.toml 파일을 활용하세요.
    API_KEY = "" 

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

# --- HTML Components ---
def render_card_header(challenge, config):
    """닫혀있을 때 보이는 카드 헤더 (4번째 사진 상단 스타일)"""
    level = challenge.get('level', 'NONE')
    c_id = str(challenge.get('challengeId'))
    points = challenge.get('value', 0)
    
    c_name = "Unknown"
    
    if config:
        names = config.get('localizedNames', {})
        ko = names.get('ko_KR') or names.get('en_US') or {}
        c_name = ko.get('name', c_name)

    icon_url = f"https://raw.communitydragon.org/latest/game/assets/challenges/config/{c_id}/tokens/{level.lower()}.png"
    color = get_tier_color(level)
    
    html = f"""
    <div class="card-header" style="border-left: 4px solid {color};">
        <div style="width:48px; height:48px; border-radius:50%; background:#121212; display:flex; justify-content:center; align-items:center; flex-shrink:0; border: 2px solid {color};">
             <img src="{icon_url}" style="width:100%; height:100%; object-fit:contain;" onerror="this.style.display='none';">
        </div>
        <div style="flex-grow:1;">
            <div class="challenge-name">{c_name}</div>
            <div class="tier-text" style="color:{color};">{level}</div>
        </div>
        <div style="text-align:right;">
            <div style="font-weight:bold; font-size:1.1em; color:#f0e6d2;">{points:,.0f}</div>
            <div class="points-text">Pts</div>
        </div>
    </div>
    """
    return html

def render_card_body(challenge, config):
    """열렸을 때 보이는 상세 내용 (4번째 사진 하단 스타일) - 버그 수정됨"""
    curr_val = challenge.get('value', 0)
    
    # 다음 목표값 계산
    next_threshold = 0
    desc = "설명 없음"
    
    if config:
        names = config.get('localizedNames', {})
        ko = names.get('ko_KR') or names.get('en_US') or {}
        desc = ko.get('description', desc).replace("<br>", " ")
        
        thresholds = config.get('thresholds', {})
        sorted_thresholds = sorted(thresholds.items(), key=lambda x: x[1])
        
        for t_name, t_val in sorted_thresholds:
            if t_val > curr_val:
                next_threshold = t_val
                break
        # 만렙(챌린저 등)이라 다음 목표가 없는 경우, 마지막 임계값을 목표로 설정
        if next_threshold == 0 and sorted_thresholds:
            next_threshold = sorted_thresholds[-1][1]

    # 퍼센트 계산 (0으로 나누기 방지)
    pct = (curr_val / next_threshold * 100) if next_threshold > 0 else 100
    pct = min(pct, 100) # 100%를 넘지 않도록
    
    # 실제 렌더링될 HTML 문자열을 생성합니다.
    html = f"""
    <div class="card-body">
        <div class="desc-text" style="margin-bottom:15px;">{desc}</div>
        
        <div class="lol-progress-frame">
            <div class="lol-progress-bar" style="width: {pct}%;"></div>
            <div class="lol-progress-text">{curr_val:,.0f} / {next_threshold:,.0f}</div>
        </div>
        
        <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
            <div class="info-text">🏆 상위 {10.5}%가 획득 (예시 데이터)</div>
            <div class="info-text">2024 시즌</div>
        </div>
        
        <div style="border-top:1px solid #333; padding-top:10px;">
            <div class="friend-text">
                <span style="font-size:1.3em;">👥</span>
                <span>친구 3명이 이 레벨에 있습니다. (예시)</span>
            </div>
        </div>
    </div>
    """
    return html

# --- Main Logic ---
if 'config' not in st.session_state:
    st.session_state.config = get_all_challenge_config()

# 어떤 카드가 열려있는지 저장하는 State
if 'expanded_ids' not in st.session_state:
    st.session_state.expanded_ids = set()

with st.sidebar:
    st.title("LoL Challenges")
    riot_id = st.text_input("Riot ID (이름#태그)", value="hide on bush#KR1")
    if st.button("검색", type="primary", use_container_width=True):
        if "#" in riot_id:
            n, t = riot_id.split('#')
            with st.spinner("정보를 불러오는 중..."):
                pid = get_puuid(n, t)
                if pid:
                    st.session_state.data = get_player_data(pid)
                    st.session_state.expanded_ids = set() # 검색 시 열림 상태 초기화
                    if 'page' in st.session_state: st.session_state.page = 1 # 페이지 초기화
                else:
                    st.error("사용자를 찾을 수 없습니다.")
        else:
            st.warning("정확한 Riot ID 형식(이름#태그)으로 입력해주세요.")

if st.session_state.get('data') and st.session_state.get('config'):
    data = st.session_state.data
    conf = st.session_state.config
    
    challenges = sorted(data.get('challenges', []), key=lambda x: x['value'], reverse=True)
    # 실제 의미 있는 도전과제만 필터링 (ID > 10)
    real_challenges = [c for c in challenges if c['challengeId'] > 10]
    
    # --- 페이지네이션 ---
    ITEMS_PER_PAGE = 20
    if 'page' not in st.session_state: st.session_state.page = 1
    total_len = len(real_challenges)
    total_pages = math.ceil(total_len / ITEMS_PER_PAGE)
    
    start_idx = (st.session_state.page - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    current_items = real_challenges[start_idx:end_idx]

    st.subheader(f"도전과제 목록 ({total_len}개)")
    st.caption(f"페이지 {st.session_state.page} / {total_pages} (총 {total_len}개 중 {start_idx+1}-{min(end_idx, total_len)} 표시)")

    # --- 2열 그리드 출력 ---
    cols = st.columns(2)
    
    for idx, item in enumerate(current_items):
        c_id = item['challengeId']
        c_id_str = str(c_id)
        config_item = conf.get(c_id_str)
        is_expanded = c_id in st.session_state.expanded_ids
        
        col_idx = idx % 2
        with cols[col_idx]:
            # 카드 컨테이너 시작
            st.markdown('<div class="challenge-card-container">', unsafe_allow_html=True)
            
            # 1. 헤더 HTML (항상 보임)
            st.markdown(render_card_header(item, config_item), unsafe_allow_html=True)
            
            # 2. 상세 내용 HTML (열렸을 때만 보임)
            if is_expanded:
                st.markdown(render_card_body(item, config_item), unsafe_allow_html=True)
            
            # 3. 토글 버튼 (헤더 아래에 붙어서 토글 기능 수행)
            btn_text = "🔼 접기" if is_expanded else "🔽 상세 정보 보기"
            if st.button(btn_text, key=f"btn_{c_id}"):
                if is_expanded:
                    st.session_state.expanded_ids.remove(c_id)
                else:
                    st.session_state.expanded_ids.add(c_id)
                st.rerun()
                
            # 카드 컨테이너 끝
            st.markdown('</div>', unsafe_allow_html=True)

    # --- 하단 페이지네이션 컨트롤 ---
    st.markdown("---")
    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("◀ 이전 페이지", use_container_width=True):
        if st.session_state.page > 1:
            st.session_state.page -= 1
            st.rerun()
    if c3.button("다음 페이지 ▶", use_container_width=True):
        if st.session_state.page < total_pages:
            st.session_state.page += 1
            st.rerun()
    c2.markdown(f"<div style='text-align:center; padding-top: 10px; font-weight:bold;'>{st.session_state.page} / {total_pages}</div>", unsafe_allow_html=True)

else:
    st.info("👈 사이드바에서 Riot ID를 입력하고 검색해주세요.")