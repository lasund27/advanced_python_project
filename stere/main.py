import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import re

# -------------------------------------------------
# 1. Page Config
# -------------------------------------------------
st.set_page_config(
    page_title="OP.GG 소환사 분석",
    page_icon="🎮",
    layout="wide"
)

# -------------------------------------------------
# 2. CSS Styling
# -------------------------------------------------
st.markdown("""
<style>
/* 전체 폰트 및 배경 */
.stApp { background-color: #010a13; color: #c8aa6e; }

/* --- 랜딩 페이지 스타일 --- */
.landing-title {
    font-size: 80px;
    font-weight: 800;
    text-align: center;
    color: #00bba3; /* OP.GG 민트색 */
    margin-bottom: 10px;
}
.landing-subtitle {
    font-size: 20px;
    text-align: center;
    color: #a09b8c;
    margin-bottom: 40px;
}
/* Streamlit 기본 인풋 스타일 커스텀 */
div[data-testid="stTextInput"] input {
    background-color: #1e2328;
    color: #f0e6d2;
    border: 1px solid #3c3c44;
    border-radius: 4px;
    height: 50px;
    font-size: 18px;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #00bba3;
    box-shadow: 0 0 0 1px #00bba3;
}

/* --- 대시보드 카드 스타일 --- */
.champ-img {
    width: 50px; height: 50px; border-radius: 50%; border: 2px solid #c8aa6e;
}
.bar-bg {
    width: 100%; height: 8px; background: #0a0a0c; border-radius: 4px; overflow: hidden; margin-bottom: 4px;
}
.bar-win {
    height: 100%; background: linear-gradient(90deg, #0ac8b9, #0a96a0);
}
.win-text { font-size: 12px; color: #0ac8b9; font-weight: bold; }

.mastery-card {
    background: #1e2328; border: 1px solid #3c3c44; border-radius: 8px; padding: 15px; text-align: center; margin-bottom: 15px;
}
.mastery-score {
    font-size: 1.2em; font-weight: bold; color: #e2b714; margin-top: 5px;
}

/* 버튼 스타일 조정 */
div.stButton > button {
    background: transparent !important;
    border: 1px solid #3c3c44 !important;
    color: #a09b8c !important;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# 3. State Management
# -------------------------------------------------
if 'riot_id' not in st.session_state:
    st.session_state.riot_id = ""

def set_search_query():
    st.session_state.riot_id = st.session_state.landing_input

def reset_search():
    st.session_state.riot_id = ""

# -------------------------------------------------
# 4. Data Fetching Functions
# -------------------------------------------------
HEADERS = {"User-Agent": "Mozilla/5.0"}

@st.cache_data(ttl=600)
def fetch_data(name, tag):
    encoded = f"{quote(name)}-{quote(tag)}"
    try:
        r_champ = requests.get(f"https://op.gg/ko/lol/summoners/kr/{encoded}/champions", headers=HEADERS)
        r_mastery = requests.get(f"https://op.gg/ko/lol/summoners/kr/{encoded}/mastery", headers=HEADERS)
        return r_champ.text, r_mastery.text
    except:
        return None, None

def parse_champs(html):
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("tbody tr")
    result = []
    for r in rows:
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
            
            result.append({
                "name": img["alt"],
                "img": img["src"],
                "wins": wins,
                "losses": losses
            })
            if len(result) == 9: break
        except: continue
    return result

def parse_mastery(html):
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select("div[data-tooltip-id^='opgg-tooltip']") 
    if not items: items = soup.select("li > div > img")

    result = []
    for item in items[:7]:
        try:
            img = item.find("img")
            score_span = item.find_next("span", string=re.compile(r"[\d,]+"))
            
            if not img: 
                if item.name == 'img': img = item
                else: continue
            
            score = score_span.text.strip() if score_span else "N/A"
            result.append({"name": img.get("alt",""), "img": img.get("src",""), "score": score})
        except: continue
    return result

# -------------------------------------------------
# 5. Main Logic (View Switching)
# -------------------------------------------------

# (A) 랜딩 페이지
if not st.session_state.riot_id:
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    st.markdown('<div class="landing-title">LOL 소환사 분석</div>', unsafe_allow_html=True)
    st.markdown('<div class="landing-subtitle">소환사별 챔피언 모스트픽 / 숙련도</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.text_input(
            "소환사명 + #Tag", 
            placeholder="ex)Hide on bush#KR1", 
            key="landing_input", 
            on_change=set_search_query
        )
        if st.button("검색", use_container_width=True):
            set_search_query()
            st.rerun()

# (B) 대시보드 페이지
else:
    # --- Sidebar ---
    with st.sidebar:
        if st.button("← 홈으로 검색", on_click=reset_search, use_container_width=True):
            pass
        st.divider()
        st.title("분석기")
        new_id = st.text_input("소환사명#태그", value=st.session_state.riot_id)
        if st.button("다시 검색", use_container_width=True):
            st.session_state.riot_id = new_id
            st.rerun()

    # --- Main Content ---
    if "#" in st.session_state.riot_id:
        name, tag = st.session_state.riot_id.split("#")
        
        # [수정된 부분] 타이틀을 한 줄에 표시하기 위한 Flex Layout 적용
        st.markdown(
            f"""
            <div style="display: flex; align-items: baseline; gap: 10px;">
                <span style="font-size: 3rem; font-weight: 700; color: #f0e6d2;">📊 {name}</span>
                <span style="font-size: 1.5rem; color: #888;">#{tag}</span>
            </div>
            <hr style="margin-top: 5px; margin-bottom: 20px; border-color: #3c3c44;">
            """,
            unsafe_allow_html=True
        )

        c_html, m_html = fetch_data(name, tag)
        
        if c_html:
            champs = parse_champs(c_html)
            mastery = parse_mastery(m_html)
            
            col1, col2 = st.columns([1.2, 0.8], gap="large")

            # --- [Left] Most Picks ---
            with col1:
                st.subheader("🎯 모스트 픽")
                st.markdown("<br>", unsafe_allow_html=True)
                
                for idx, c in enumerate(champs):
                    total = c['wins'] + c['losses']
                    winrate = int(c['wins'] / total * 100) if total > 0 else 0
                    
                    c_col1, c_col2 = st.columns([4, 2])
                    with c_col1:
                        st.markdown(f"""
                        <div style="display:flex; align-items:center; gap:15px;">
                            <img src="{c['img']}" class="champ-img">
                            <div>
                                <div style="color:#f0e6d2; font-weight:bold;">{c['name']}</div>
                                <div style="color:#888; font-size:12px;">{c['wins']}승 {c['losses']}패</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    with c_col2:
                        st.markdown(f"""
                        <div style="display:flex; flex-direction:column; justify-content:center; height:100%;">
                            <div class="bar-bg" style="width:120px;">
                                <div class="bar-win" style="width:{winrate}%"></div>
                            </div>
                            <div class="win-text">{winrate}% 승률</div>
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown("<hr style='margin:5px 0; border-color:#2c3036;'>", unsafe_allow_html=True)

            # --- [Right] Mastery ---
            with col2:
                st.subheader("🏅 숙련도")
                st.markdown("<br>", unsafe_allow_html=True)
                
                cols = st.columns(2)
                for i, m in enumerate(mastery):
                    with cols[i % 2]:
                        st.markdown(f"""
                        <div class="mastery-card">
                            <img src="{m['img']}" width="60" style="border-radius:50%; border:2px solid #e2b714;">
                            <div style="margin-top:10px; font-weight:bold;">{m['name']}</div>
                            <div class="mastery-score">{m['score']}</div>
                            <div style="font-size:10px; color:#666;">Points</div>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.error("데이터를 불러오지 못했습니다. 닉네임을 확인해주세요.")
    else:
        st.warning("형식이 올바르지 않습니다. (예: Hide on bush#KR1)")