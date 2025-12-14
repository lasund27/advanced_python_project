import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import re

# -------------------------------------------------
# Page Config
# -------------------------------------------------
st.set_page_config(
    page_title="OP.GG 소환사 분석",
    page_icon="🎮",
    layout="wide"
)

# -------------------------------------------------
# CSS
# -------------------------------------------------
st.markdown("""
<style>
.stApp { background-color:#010a13; color:#c8aa6e; }

.block-container {
    padding-top:5rem !important;
    padding-bottom:5rem;
    max-width:1400px;
}

[data-testid="stSidebar"] {
    background-color:#091428;
    border-right:1px solid #1e282d;
}
[data-testid="stSidebar"] * { color:#cdbe91 !important; }

.grid {
    display:grid;
    grid-template-columns:repeat(auto-fill, minmax(220px,1fr));
    gap:15px;
    margin-top:20px;
}

.card {
    background:#1e2328;
    border:2px solid #3c3c44;
    border-radius:6px;
    padding:15px;
    text-align:center;
    transition:.2s;

    min-height:230px;              /* ✅ 세로 높이 통일 */
    display:flex;
    flex-direction:column;
    justify-content:space-between;
}

.card:hover {
    transform:translateY(-5px);
    border-color:#f0e6d2;
}

.title { font-weight:bold; color:#f0e6d2; margin-top:10px; }
.sub { font-size:.85em; color:#a09b8c; }

.bar-bg {
    width:100%;
    height:18px;
    background:#0a0a0c;
    border-radius:9px;
    overflow:hidden;
    margin-top:8px;
}
.bar-win {
    height:100%;
    border-radius:9px;
    background:linear-gradient(90deg,#0ac8b9,#0a96a0);
}

button {
    background:#1e2328 !important;
    color:#c8aa6e !important;
    border:1px solid #c8aa6e !important;
}
button:hover {
    background:#c8aa6e !important;
    color:#010a13 !important;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# Sidebar
# -------------------------------------------------
with st.sidebar:
    st.title("OP.GG 분석기")
    riot_id = st.text_input("소환사명#태그", value="Hide on bush#KR1")
    search = st.button("검색", use_container_width=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

def fetch(url):
    r = requests.get(url, headers=HEADERS)
    return r.text if r.status_code == 200 else None

# -------------------------------------------------
# Parse Functions
# -------------------------------------------------
def parse_most_champions(html):
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("tbody tr")
    result = []

    for r in rows:
        text = r.get_text(" ", strip=True).lower()
        if "vs" in text:
            continue

        img = r.find("img")
        if not img:
            continue

        w = re.search(r"(\d+)\s*승", text)
        l = re.search(r"(\d+)\s*패", text)
        if not w or not l:
            continue

        wins, losses = int(w.group(1)), int(l.group(1))
        if wins + losses == 0:
            continue

        result.append({
            "name": img["alt"],
            "img": img["src"],
            "wins": wins,
            "losses": losses
        })

        if len(result) == 5:
            break

    return result

def parse_mastery(html):
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("div[data-tooltip-id='opgg-tooltip']")[:6]
    result = []

    for r in rows:
        img = r.find("img")
        score = r.find("span", class_="mx-auto")
        if not img:
            continue

        result.append({
            "name": img["alt"],
            "img": img["src"],
            "score": score.text.strip() if score else "-"
        })

    return result

# -------------------------------------------------
# Main
# -------------------------------------------------
if search and "#" in riot_id:
    name, tag = riot_id.split("#")
    encoded = f"{quote(name)}-{quote(tag)}"

    champ_html = fetch(f"https://op.gg/ko/lol/summoners/kr/{encoded}/champions")
    mastery_html = fetch(f"https://op.gg/ko/lol/summoners/kr/{encoded}/mastery")

    if not champ_html:
        st.error("데이터를 불러오지 못했습니다.")
        st.stop()

    champs = parse_most_champions(champ_html)
    mastery = parse_mastery(mastery_html)

    col_left, col_right = st.columns([1, 1])

    # ---------------- Most Pick ----------------
    with col_left:
        st.markdown("## 🎯 모스트 픽")
        st.markdown("<div class='grid'>", unsafe_allow_html=True)

        for c in champs:
            total = c["wins"] + c["losses"]
            winrate = int(c["wins"] / total * 100)

            st.markdown(f"""
            <div class="card">
                <div>
                    <img src="{c['img']}" width="80">
                    <div class="title">{c['name']}</div>
                    <div class="sub">{c['wins']}승 {c['losses']}패</div>
                </div>
                <div>
                    <div class="bar-bg">
                        <div class="bar-win" style="width:{winrate}%"></div>
                    </div>
                    <div class="sub">{winrate}% 승률</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # ---------------- Mastery ----------------
    with col_right:
        st.markdown("## 🏅 숙련도")
        st.markdown("<div class='grid'>", unsafe_allow_html=True)

        for m in mastery:
            st.markdown(f"""
            <div class="card">
                <div>
                    <img src="{m['img']}" width="80">
                    <div class="title">{m['name']}</div>
                </div>
                <div class="sub">{m['score']} pts</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

else:
    st.info("👈 사이드바에서 소환사명을 입력하세요.")
