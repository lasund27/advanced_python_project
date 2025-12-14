import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import re

# ---------------------------------------------------------------
# 기본 설정
# ---------------------------------------------------------------
st.set_page_config(
    page_title="OP.GG 소환사 분석",
    page_icon="🎮",
    layout="wide"
)
st.title("🎮 OP.GG 소환사 분석")

# ---------------------------------------------------------------
# 소환사 입력
# ---------------------------------------------------------------
user_input = st.text_input("소환사 이름 (닉네임#태그)")

if not user_input or "#" not in user_input:
    st.info("예: Hide on bush#KR1")
    st.stop()

name, tag = user_input.split("#", 1)
encoded = f"{quote(name)}-{quote(tag)}"

BASE = "https://op.gg/ko/lol/summoners/kr"
URL_CHAMP = f"{BASE}/{encoded}/champions"
URL_MASTERY = f"{BASE}/{encoded}/mastery"

HEADERS = {"User-Agent": "Mozilla/5.0"}

# ---------------------------------------------------------------
# HTML 요청
# ---------------------------------------------------------------
def fetch(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        return r.text
    except:
        return None

# ---------------------------------------------------------------
# 모스트픽 파싱 (상대전적 제거)
# ---------------------------------------------------------------
def parse_champions(html):
    soup = BeautifulSoup(html, "html.parser")
    champs = []

    rows = soup.select("tbody tr")

    for r in rows:
        text = r.get_text(" ", strip=True).lower()

        # ❌ 상대전적(vs ○○) 제거
        if "vs" in text:
            continue

        img = r.find("img")
        if not img:
            continue

        wins = re.search(r"(\d+)\s*승", text)
        losses = re.search(r"(\d+)\s*패", text)

        if not wins or not losses:
            continue

        champs.append({
            "img": img.get("src"),
            "name": img.get("alt", "Unknown"),
            "wins": int(wins.group(1)),
            "losses": int(losses.group(1))
        })

        if len(champs) == 5:
            break

    return champs

# ---------------------------------------------------------------
# 숙련도 파싱
# ---------------------------------------------------------------
def parse_mastery(html):
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("div[data-tooltip-id='opgg-tooltip']")[:5]
    result = []

    for r in rows:
        img = r.find("img")
        score = r.find("span", class_="mx-auto")
        level = r.find("span", class_="text-2xs")

        if not img:
            continue

        result.append({
            "img": img.get("src"),
            "name": img.get("alt", "Unknown"),
            "score": score.text if score else "-",
            "level": level.text if level else "-"
        })

    return result

# ---------------------------------------------------------------
# 데이터 로드
# ---------------------------------------------------------------
html_champ = fetch(URL_CHAMP)
html_mastery = fetch(URL_MASTERY)

if not html_champ or not html_mastery:
    st.error("OP.GG 데이터를 불러오지 못했습니다.")
    st.stop()

left, divider, right = st.columns([3, 0.15, 3])

# =========================
# 🎯 모스트 픽
# =========================
with left:
    st.subheader("🎯 모스트픽 Top 5")

    st.markdown("""
    <style>
    .bar-wrap {width:100%; height:18px; background:#ddd; border-radius:6px; display:flex;}
    .win {background:#4da6ff;}
    .loss {background:#ff4d4d;}
    </style>
    """, unsafe_allow_html=True)

    for c in parse_champions(html_champ):
        total = c["wins"] + c["losses"]
        win_p = c["wins"] / total * 100 if total else 0
        loss_p = 100 - win_p

        img_col, graph_col = st.columns([1, 3])

        with img_col:
            st.image(c["img"], width=60)

        with graph_col:
            st.write(f"**{c['name']}**")
            st.markdown(
                f"<div>{c['wins']}승 <span style='float:right'>{c['losses']}패</span></div>"
                f"<div class='bar-wrap'>"
                f"<div class='win' style='width:{win_p}%'></div>"
                f"<div class='loss' style='width:{loss_p}%'></div>"
                f"</div>",
                unsafe_allow_html=True
            )

        st.markdown("---")

# =========================
# 경계선
# =========================
with divider:
    st.markdown(
        "<div style='height:100%; border-left:3px solid #777;'></div>",
        unsafe_allow_html=True
    )

# =========================
# 🏅 숙련도
# =========================
with right:
    st.subheader("🏅 숙련도 Top 5")

    for m in parse_mastery(html_mastery):
        c1, c2 = st.columns([1, 3])
        with c1:
            st.image(m["img"], width=60)
        with c2:
            st.write(f"**{m['name']}**")
            st.write(f"점수: {m['score']}")
            st.write(f"레벨: {m['level']}")
        st.markdown("---")
