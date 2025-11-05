import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import pandas as pd
import re

st.set_page_config(page_title="OP.GG Summoner Snapshot", layout="wide")

st.title("🎮 OP.GG 요약: 숙련도 Top 5 & 모스트픽 Top 5")

# 닉네임 입력
user_input = st.text_input("소환사 이름을 입력하세요 (예: Hide on bush#KR1)", value="")

if not user_input:
    st.info("닉네임#태그 형태로 입력해주세요.")
    st.stop()

# 입력 형태 변환: nickname#tag → nickname-tag
if "#" not in user_input:
    st.error("입력 형식이 잘못되었습니다. 예: nickname#tag")
    st.stop()

nickname, tag = user_input.split("#", 1)
encoded_name = f"{quote(nickname)}-{quote(tag)}"

# URL 구성
BASE_URL = "https://op.gg/ko/lol/summoners/kr"
MASTERY_URL = f"{BASE_URL}/{encoded_name}/mastery"
CHAMPIONS_URL = f"{BASE_URL}/{encoded_name}/champions"

# 요청 헤더
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122 Safari/537.36"
}

# HTML 요청 함수
def fetch(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        return res.text
    except Exception as e:
        st.error(f"페이지 불러오기 실패: {e}")
        return None

# 숙련도 파싱 함수
def parse_mastery(html):
    soup = BeautifulSoup(html, "html.parser")
    champs = []
    items = soup.select("div.MasteryChampionList div.champion, div.MasteryChampionItem")

    for i, item in enumerate(items[:5]):
        img = item.select_one("img[src*='champion']")
        badge = item.select_one("img[src*='mastery']")
        name = img.get("alt") if img else "Unknown"
        score_el = item.find(string=re.compile(r"[0-9,]+"))
        score = score_el.strip() if score_el else "-"
        champs.append({
            "name": name,
            "img": img["src"] if img else None,
            "badge": badge["src"] if badge else None,
            "score": score
        })
    return champs

# 챔피언(모스트픽) 파싱 함수
def parse_champions(html):
    soup = BeautifulSoup(html, "html.parser")
    champs = []
    rows = soup.select("div.champion, div.ChampionBox, tr")

    for r in rows[:5]:
        img = r.select_one("img[src*='champion']")
        name = img.get("alt") if img else "Unknown"
        text = r.get_text(" ", strip=True)
        winrate = re.search(r"(\d{1,3}\.?\d*)%", text)
        wins = re.search(r"(\d+)\s*승", text)
        losses = re.search(r"(\d+)\s*패", text)

        champs.append({
            "name": name,
            "img": img["src"] if img else None,
            "winrate": winrate.group(1) + "%" if winrate else "-",
            "wins": wins.group(1) if wins else "-",
            "losses": losses.group(1) if losses else "-"
        })
    return champs

# 페이지 요청
with st.spinner("OP.GG에서 데이터 불러오는 중..."):
    mastery_html = fetch(MASTERY_URL)
    champions_html = fetch(CHAMPIONS_URL)

if not mastery_html:
    st.error("숙련도 페이지를 불러오지 못했습니다.")
    st.stop()

# 데이터 파싱
mastery_list = parse_mastery(mastery_html)
champ_list = parse_champions(champions_html) if champions_html else []

# ------------------------
# 출력
# ------------------------
col1, col2 = st.columns(2)

# 숙련도 Top5
with col1:
    st.header("🏅 숙련도 Top 5")
    if not mastery_list:
        st.write("숙련도 정보를 찾지 못했습니다.")
    else:
        for i, c in enumerate(mastery_list, start=1):
            cols = st.columns([1, 3])
            with cols[0]:
                if c["img"]:
                    st.image(c["img"], width=70)
            with cols[1]:
                st.subheader(f"{i}. {c['name']}")
                st.write(f"숙련도 점수: {c['score']}")
                if c["badge"]:
                    st.image(c["badge"], width=30)

# 모스트픽 Top5
with col2:
    st.header("🔥 모스트픽 Top 5")
    if not champ_list:
        st.write("챔피언 정보를 찾지 못했습니다.")
    else:
        table_data = [
            [c["name"], c["winrate"], c["wins"], c["losses"]]
            for c in champ_list
        ]
        df = pd.DataFrame(table_data, columns=["챔피언", "승률", "승리 수", "패배 수"])
        st.table(df)

st.markdown("---")
st.caption(f"데이터 출처: [OP.GG]({MASTERY_URL})")
