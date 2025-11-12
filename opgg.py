import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import pandas as pd
import re

st.set_page_config(page_title="OP.GG 챔피언 요약", layout="wide")

st.title("🔥 OP.GG 챔피언 분석기")

# --- 입력 ---
user_input = st.text_input("소환사 이름을 입력하세요 (예: lasund72#7227)", value="")

if not user_input or "#" not in user_input:
    st.info("닉네임#태그 형태로 입력해주세요. 예: Hide on bush#KR1")
    st.stop()

nickname, tag = user_input.split("#", 1)
encoded_name = f"{quote(nickname)}-{quote(tag)}"

# --- URL 구성 ---
BASE_URL = "https://op.gg/ko/lol/summoners/kr"
CHAMPIONS_URL = f"{BASE_URL}/{encoded_name}/champions"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122 Safari/537.36"
}

# --- HTML 요청 ---
def fetch(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        return res.text
    except Exception as e:
        st.error(f"페이지 요청 실패: {e}")
        return None

# --- 챔피언 페이지 파싱 ---
def parse_champions(html):
    soup = BeautifulSoup(html, "html.parser")

    champs = []
    rows = soup.select("tr, div.ChampionBox, div.champion")  # 유연한 선택자

    # “모든 챔피언” 행을 제외하기 위해 첫 번째 행 스킵
    valid_rows = []
    for r in rows:
        text = r.get_text(" ", strip=True)
        if "모든 챔피언" in text:
            continue  # skip this
        if "vs" in text:
            continue  # skip VS 데이터
        if re.search(r"승|패|%", text):  # 챔피언 통계가 포함된 행만
            valid_rows.append(r)

    # 상위 5개만
    valid_rows = valid_rows[:5]

    for r in valid_rows:
        img_tag = r.select_one("img[src*='champion']")
        img = img_tag.get("src") if img_tag else None
        name = img_tag.get("alt") if img_tag else "Unknown"

        text = r.get_text(" ", strip=True)
        winrate = re.search(r"(\d{1,3}\.?\d*)%", text)
        wins = re.search(r"(\d+)\s*승", text)
        losses = re.search(r"(\d+)\s*패", text)

        champs.append({
            "name": name,
            "img": img,
            "winrate": winrate.group(1) + "%" if winrate else "-",
            "wins": wins.group(1) if wins else "-",
            "losses": losses.group(1) if losses else "-"
        })

    return champs

# --- 실행 ---
with st.spinner("OP.GG에서 챔피언 데이터를 불러오는 중..."):
    html = fetch(CHAMPIONS_URL)

if not html:
    st.error("페이지를 불러오지 못했습니다.")
    st.stop()

champions = parse_champions(html)

if not champions:
    st.warning("챔피언 데이터를 찾지 못했습니다. 잠시 후 다시 시도해주세요.")
    st.stop()

# --- 출력 ---
st.header("🎯 모스트픽 챔피언 Top 5")

for i, c in enumerate(champions, start=1):
    cols = st.columns([1, 4])
    with cols[0]:
        if c["img"]:
            st.image(c["img"], width=70)
    with cols[1]:
        st.subheader(f"{i}. {c['name']}")
        st.write(f"승률: **{c['winrate']}**")
        st.write(f"승리: {c['wins']}회 / 패배: {c['losses']}회")

st.markdown("---")
st.caption(f"데이터 출처: [OP.GG]({CHAMPIONS_URL})")
