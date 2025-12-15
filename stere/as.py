import streamlit as st
import requests
import urllib.parse
import plotly.graph_objects as go
import math
import random
import time

# --- 페이지 설정 ---
st.set_page_config(page_title="롤 도전과제 검색기", page_icon="🏆", layout="wide")

# --- 커스텀 CSS ---
st.markdown("""
<style>
    /* 전체 스타일 */
    .stApp { background-color: #010a13; color: #c8aa6e; }
    .block-container { padding-top: 2rem !important; max-width: 1200px; }
    
    /* 사이드바 */
    [data-testid="stSidebar"] { background-color: #091428; border-right: 1px solid #1e282d; }
    [data-testid="stSidebar"] * { color: #cdbe91 !important; }

    /* 기본 카드 스타일 */
    .challenge-card-inner {
        background-color: #1e2328;
        border: 2px solid #3c3c44;
        border-radius: 6px;
        padding: 15px 10px;
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        height: 320px; 
        justify-content: flex-start;
        position: relative;
        transition: all 0.2s ease;
    }
    
    /* 승급 임박 카드 강조 스타일 */
    .imminent-card {
        border: 2px solid #d13639 !important;
        background-color: #2a1e1e !important;
        box-shadow: 0 0 10px rgba(209, 54, 57, 0.2);
    }
    .imminent-badge {
        background-color: #d13639;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8em;
        font-weight: bold;
        margin-bottom: 5px;
    }

    /* 칭호 보상 배지 스타일 */
    .title-reward-badge {
        position: absolute;
        top: 10px;
        right: 10px;
        background-color: #ffd700;
        color: #000;
        font-size: 0.7em;
        font-weight: bold;
        padding: 2px 6px;
        border-radius: 4px;
        z-index: 5;
        box-shadow: 0 0 5px rgba(255, 215, 0, 0.5);
    }

    /* 랜덤 추첨 카드 스타일 */
    .spinning-card-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 30px; 
        height: 400px; 
    }

    .spinning-card {
        border-color: #c8aa6e !important;
        box-shadow: 0 0 25px rgba(200, 170, 110, 0.5); 
        width: 350px !important; 
        height: 380px !important; 
        transform: scale(1.05); 
        z-index: 10; 
    }
    
    .card-icon-area { width: 70px; height: 70px; margin-bottom: 10px; flex-shrink: 0; }
    .spinning-card .card-icon-area { width: 100px; height: 100px; }

    .card-title {
        color: #f0e6d2; font-weight: bold; font-size: 1.1em; line-height: 1.3;
        margin: 5px 0; height: 45px; overflow: hidden;
        display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
    }
    .spinning-card .card-title { font-size: 1.4em; height: auto; -webkit-line-clamp: 3; }

    .card-desc {
        color: #a09b8c; font-size: 0.8em; line-height: 1.4; margin-bottom: 10px;
        height: 55px; overflow: hidden;
        display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical;
    }

    .card-footer { margin-top: auto; width: 100%; }

    /* 모달 및 기타 */
    .modal-stat-box { background-color: #1a1c21; padding: 15px; border-radius: 10px; margin-top: 10px; border: 1px solid #333; }
    
    div.stButton > button { width: 100%; background-color: #1e2328; color: #c8aa6e; border: 1px solid #c8aa6e; }
    div.stButton > button:hover { background-color: #c8aa6e; color: #010a13; border-color: #f0e6d2; }
    
    div[data-testid="stTextInput"] input { background-color: #1e2328; color: #f0e6d2; border: 1px solid #3c3c44; }
</style>
""", unsafe_allow_html=True)

# --- API 키 설정 ---
if "API_KEY" in st.secrets:
    API_KEY = st.secrets["API_KEY"]
else:
    API_KEY = "" # ⚠️ 여기에 본인의 라이엇 API 키를 입력하세요!

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

def calculate_next_level(challenge_info, config_info):
    current_val = challenge_info.get('value', 0)
    current_level = challenge_info.get('level', 'NONE')
    thresholds = config_info.get('thresholds', {})
    
    order = ['IRON', 'BRONZE', 'SILVER', 'GOLD', 'PLATINUM', 'DIAMOND', 'MASTER', 'GRANDMASTER', 'CHALLENGER']
    
    next_tier = "MAX"
    next_threshold = current_val
    prev_threshold = 0
    
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

def has_title_reward(config_item):
    thresholds = config_item.get('thresholds', {})
    for tier, val in thresholds.items():
        if isinstance(val, dict) and 'rewards' in val:
            for reward in val['rewards']:
                if reward.get('type') == 'TITLE':
                    return True
    return False

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

# --- 상세 정보 팝업 (모달) ---
@st.dialog("도전과제 상세 정보")
def show_detail_modal(challenge_data, config_data):
    c_id = str(challenge_data.get('challengeId'))
    current_val = challenge_data.get('value', 0)
    level = challenge_data.get('level', 'NONE')
    percentile = challenge_data.get('percentile', 0) * 100 

    names = config_data.get('localizedNames', {})
    ko = names.get('ko_KR') or names.get('en_US') or {}
    c_name = ko.get('name', f"Unknown ({c_id})")
    c_desc = ko.get('description', '설명 없음').replace("<br>", " ")
    
    color = get_tier_color(level)
    icon_url = f"https://raw.communitydragon.org/latest/game/assets/challenges/config/{c_id}/tokens/{level.lower()}.png"

    col1, col2 = st.columns([1, 3])
    with col1:
        st.image(icon_url, width=100)
    with col2:
        st.markdown(f"<h3 style='margin:0; color:#f0e6d2'>{c_name}</h3>", unsafe_allow_html=True)
        st.markdown(f"<span style='color:{color}; font-weight:bold; font-size:1.2em'>{level}</span>", unsafe_allow_html=True)
        if percentile > 0:
            st.caption(f"👥 플레이어 중 상위 {percentile:.1f}%가 획득")
    
    st.divider()
    st.info(c_desc)

    next_tier, prev_th, next_th = calculate_next_level(challenge_data, config_data)
    
    if next_tier == "MAX":
        st.balloons()
        st.success("🏆 모든 단계를 완료했습니다!")
        st.metric(label="현재 점수", value=f"{current_val:,.0f} Pts")
    else:
        range_val = next_th - prev_th
        current_progress = current_val - prev_th
        if range_val <= 0: range_val = 1 
        ratio = min(max(current_progress / range_val, 0.0), 1.0) 
        
        st.markdown(f"#### 다음 단계: <span style='color:{get_tier_color(next_tier)}'>{next_tier}</span>", unsafe_allow_html=True)
        msg = f"목표까지 {next_th - current_val:,.0f} 남음"

        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; font-size:0.8em; color:#aaa; margin-bottom:5px;">
            <span>{current_val:,.0f}</span>
            <span>{next_th:,.0f}</span>
        </div>
        <div style="width:100%; background:#333; height:10px; border-radius:5px; overflow:hidden;">
            <div style="width:{ratio*100}%; background:linear-gradient(90deg, {color}, {get_tier_color(next_tier)}); height:100%;"></div>
        </div>
        <div style="text-align:right; font-size:0.8em; color:#aaa; margin-top:5px;">
            {msg}
        </div>
        """, unsafe_allow_html=True)

# --- Main Logic ---
if 'config' not in st.session_state:
    st.session_state.config = get_all_challenge_config()
if 'page_num' not in st.session_state:
    st.session_state.page_num = 1
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""

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
                    st.session_state.page_num = 1
                else:
                    st.error("사용자 없음")
    
    st.markdown("---")
    # [신규] 정렬 옵션 추가
    sort_option = st.selectbox(
        "정렬 기준",
        ["점수 높은 순", "점수 낮은 순", "티어 높은 순", "티어 낮은 순"]
    )
    
    st.markdown("---")
    show_imminent = st.checkbox("🔥 승급 임박 추천 보기", value=False)
    # [수정] 칭호 필터링 체크박스 삭제됨

if st.session_state.get('data') and st.session_state.get('config'):
    data = st.session_state.data
    conf = st.session_state.config
    
    total = data.get('totalPoints', {})
    cur = total.get('current', 0)
    maxx = total.get('max', 20000)
    tier = total.get('level', 'IRON')

    # 상단 전체 진행도
    c1, c2 = st.columns([1, 4])
    with c1:
        st.plotly_chart(make_donut(cur, maxx, tier), use_container_width=True, config={'displayModeBar':False})
    with c2:
        per = min((cur/maxx*100), 100)
        st.markdown(f"""
        <div style="padding: 20px;">
            <h1 style="margin:0; color:#f0e6d2; font-size:2.5em;">전체 진행도</h1>
            <div style="background-color:#0a0a0c; height:20px; border-radius:10px; border:1px solid #444; margin-top:10px; position:relative; overflow:hidden;">
                <div style="width:{per}%; background:linear-gradient(90deg, #0ac8b9, #0a96a0); height:100%;"></div>
                <div style="position:absolute; top:0; width:100%; text-align:center; font-size:12px; line-height:20px; color:white; text-shadow:1px 1px 2px black;">
                    {cur:,} / {maxx:,}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 데이터 준비
    challenges = sorted(data.get('challenges', []), key=lambda x: x['value'], reverse=True)
    real_challenges = [c for c in challenges if c['challengeId'] > 10]

    # [UI] 승급 임박 표시 로직 (체크박스 활성화 시)
    if show_imminent:
        imminent_list = []
        for c in real_challenges:
            c_id = str(c['challengeId'])
            cfg = conf.get(c_id, {})
            next_tier, _, next_th = calculate_next_level(c, cfg)
            
            if next_tier != "MAX" and c['value'] < next_th:
                diff = next_th - c['value']
                imminent_list.append({
                    'diff': diff, 'data': c, 'config': cfg, 'next_tier': next_tier
                })
        
        imminent_list.sort(key=lambda x: x['diff'])
        top_imminent = imminent_list[:5]

        if top_imminent:
            st.markdown("### 🔥 승급까지 한 걸음! (승급 임박 TOP 5)")
            i_cols = st.columns(5)
            for idx, item in enumerate(top_imminent):
                c_data = item['data']
                c_conf = item['config']
                diff = item['diff']
                next_tier = item['next_tier']
                
                names = c_conf.get('localizedNames', {})
                ko = names.get('ko_KR') or names.get('en_US') or {}
                c_name = ko.get('name', 'Unknown')
                c_desc = ko.get('description', '')[:30] + "..." if len(ko.get('description', '')) > 30 else ko.get('description', '')
                
                curr_level = c_data.get('level', 'NONE')
                color = get_tier_color(curr_level)
                icon_url = f"https://raw.communitydragon.org/latest/game/assets/challenges/config/{c_data.get('challengeId')}/tokens/{curr_level.lower()}.png"

                with i_cols[idx]:
                    card_html = (
                        f'<div class="challenge-card-inner imminent-card" style="height: 280px; margin-bottom: 10px;">'
                        f'  <div class="imminent-badge">D-{diff:,.0f}점</div>'
                        f'  <div class="card-icon-area" style="width:50px; height:50px; background:#121212; border-radius:50%; display:flex; justify-content:center; align-items:center;">'
                        f'    <img src="{icon_url}" style="width:100%; height:100%; object-fit:contain;" onerror="this.style.display=\'none\';">'
                        f'  </div>'
                        f'  <div class="card-title" style="font-size:1em; height:40px;">{c_name}</div>'
                        f'  <div class="card-desc" style="font-size:0.75em; height:40px;">{c_desc}</div>'
                        f'  <div class="card-footer">'
                        f'    <div style="font-size:0.8em; color:#aaa;">Next: <span style="color:{get_tier_color(next_tier)}">{next_tier}</span></div>'
                        f'  </div>'
                        f'</div>'
                    )
                    st.markdown(card_html, unsafe_allow_html=True)
                    if st.button("상세", key=f"btn_imm_{c_data.get('challengeId')}", use_container_width=True):
                        show_detail_modal(c_data, c_conf)
            st.divider()

    # 애니메이션 공간
    spin_placeholder = st.empty()

    # 검색창 + 랜덤 추천
    col_search, col_rand = st.columns([3, 1], vertical_alignment="bottom")
    with col_search:
        search_input = st.text_input("🔍 도전과제 검색 (이름, 내용)", placeholder="예: 무작위 총력전, 펜타킬...", value=st.session_state.search_query)

    with col_rand:
        if st.button("🎲 오늘의 도전과제", use_container_width=True, type="primary"):
            if real_challenges:
                for i in range(15):
                    temp_pick = random.choice(real_challenges)
                    c_id_temp = str(temp_pick['challengeId'])
                    config_temp = conf.get(c_id_temp, {})
                    names_temp = config_temp.get('localizedNames', {})
                    ko_temp = names_temp.get('ko_KR') or names_temp.get('en_US') or {}
                    c_name_temp = ko_temp.get('name', "Unknown")
                    level_temp = temp_pick.get('level', 'NONE')
                    color_temp = get_tier_color(level_temp)
                    icon_url_temp = f"https://raw.communitydragon.org/latest/game/assets/challenges/config/{c_id_temp}/tokens/{level_temp.lower()}.png"

                    temp_html = (
                        f'<div class="spinning-card-container">'
                        f'  <div class="challenge-card-inner spinning-card" style="border-bottom: 4px solid {color_temp}; opacity:0.9;">'
                        f'    <div style="color:#c8aa6e; font-weight:bold; font-size:1.2em; margin-bottom:15px;">🎲 추첨 중...</div>'
                        f'    <div class="card-icon-area" style="background:#121212; border-radius:50%; display:flex; justify-content:center; align-items:center;">'
                        f'      <img src="{icon_url_temp}" style="width:100%; height:100%; object-fit:contain;">'
                        f'    </div>'
                        f'    <div class="card-title">{c_name_temp}</div>'
                        f'    <div style="color:{color_temp}; font-weight:bold; font-size:1.2em; margin-top:10px;">{level_temp}</div>'
                        f'  </div>'
                        f'</div>'
                    )
                    spin_placeholder.markdown(temp_html, unsafe_allow_html=True)
                    time.sleep(0.05 + i * 0.01)

                spin_placeholder.empty()
                random_pick = random.choice(real_challenges)
                pick_config = conf.get(str(random_pick['challengeId']), {})
                show_detail_modal(random_pick, pick_config)
            else:
                st.toast("추천할 도전과제가 없습니다.")

    # 검색 및 필터링 로직 (탭 & 칭호 & 검색)
    if search_input != st.session_state.search_query:
        st.session_state.search_query = search_input
        st.session_state.page_num = 1
        st.rerun()

    filtered_challenges = []
    
    query = search_input.lower().strip() if search_input.strip() else ""

    for c in real_challenges:
        c_id = str(c['challengeId'])
        config_item = conf.get(c_id, {})
        
        # [수정] 칭호 필터링 삭제됨 (조건문 제거)

        # 필터 2: 검색어
        names = config_item.get('localizedNames', {})
        ko = names.get('ko_KR') or names.get('en_US') or {}
        c_name = ko.get('name', '').lower()
        c_desc = ko.get('description', '').lower()
        
        if query and (query not in c_name and query not in c_desc):
            continue
            
        filtered_challenges.append(c)

    # [신규] 정렬 로직 적용
    # 티어 순서 정의 (낮은 순 -> 높은 순)
    tier_order_list = ['NONE', 'IRON', 'BRONZE', 'SILVER', 'GOLD', 'PLATINUM', 'DIAMOND', 'MASTER', 'GRANDMASTER', 'CHALLENGER']
    
    if sort_option == "점수 높은 순":
        filtered_challenges.sort(key=lambda x: x.get('value', 0), reverse=True)
    elif sort_option == "점수 낮은 순":
        filtered_challenges.sort(key=lambda x: x.get('value', 0))
    elif sort_option == "티어 높은 순":
        filtered_challenges.sort(key=lambda x: tier_order_list.index(x.get('level', 'NONE')), reverse=True)
    elif sort_option == "티어 낮은 순":
        filtered_challenges.sort(key=lambda x: tier_order_list.index(x.get('level', 'NONE')))

    if not filtered_challenges:
        st.warning(f"조건에 맞는 도전과제가 없습니다.")
    else:
        ITEMS_PER_PAGE = 20
        total_items = len(filtered_challenges)
        total_pages = math.ceil(total_items / ITEMS_PER_PAGE)
        
        if st.session_state.page_num > total_pages:
            st.session_state.page_num = 1
        
        col_prev, col_info, col_next = st.columns([1, 2, 1])
        with col_prev:
            if st.button("◀ 이전", use_container_width=True, key="prev_btn"):
                if st.session_state.page_num > 1:
                    st.session_state.page_num -= 1
                    st.rerun()
        with col_next:
            if st.button("다음 ▶", use_container_width=True, key="next_btn"):
                if st.session_state.page_num < total_pages:
                    st.session_state.page_num += 1
                    st.rerun()
        with col_info:
            st.markdown(f"<div style='text-align:center; padding-top:10px;'>Page {st.session_state.page_num} / {total_pages} (검색: {total_items}개)</div>", unsafe_allow_html=True)

        start_idx = (st.session_state.page_num - 1) * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        current_page_data = filtered_challenges[start_idx:end_idx]

        cols = st.columns(4)
        
        for i, challenge in enumerate(current_page_data):
            c_id = str(challenge.get('challengeId'))
            config_item = conf.get(c_id, {})
            
            points = challenge.get('value', 0)
            level = challenge.get('level', 'NONE')
            
            names = config_item.get('localizedNames', {})
            ko = names.get('ko_KR') or names.get('en_US') or {}
            c_name = ko.get('name', f"Unknown")
            c_desc = ko.get('description', '설명 없음')
            
            color = get_tier_color(level)
            icon_url = f"https://raw.communitydragon.org/latest/game/assets/challenges/config/{c_id}/tokens/{level.lower()}.png"

            title_badge_html = ""
            if has_title_reward(config_item):
                title_badge_html = '<div class="title-reward-badge">👑 TITLE</div>'

            with cols[i % 4]:
                # [수정] 한 줄 연결 방식 (들여쓰기 오류 방지)
                card_html = (
                    f'<div class="challenge-card-inner" style="border-bottom: 4px solid {color}; margin-bottom: 5px;">'
                    f'  {title_badge_html}'
                    f'  <div class="card-icon-area" style="background:#121212; border-radius:50%; display:flex; justify-content:center; align-items:center;">'
                    f'    <img src="{icon_url}" style="width:100%; height:100%; object-fit:contain;" onerror="this.style.display=\'none\';">'
                    f'  </div>'
                    f'  <div class="card-title">{c_name}</div>'
                    f'  <div class="card-desc">{c_desc}</div>'
                    f'  <div class="card-footer">'
                    f'    <div style="color:{color}; font-weight:bold; font-size:1.1em;">{points:,.0f} Pts</div>'
                    f'    <div style="color:{color}; font-size:0.9em;">{level}</div>'
                    f'  </div>'
                    f'</div>'
                )
                st.markdown(card_html, unsafe_allow_html=True)
                
                if st.button("상세 정보", key=f"btn_{c_id}", use_container_width=True):
                    show_detail_modal(challenge, config_item)

        st.markdown("<br><br>", unsafe_allow_html=True)

else:
    if not st.session_state.get('data'):
        st.info("👈 사이드바에서 아이디를 입력하고 검색하세요.")