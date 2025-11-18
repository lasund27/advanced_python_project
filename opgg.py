import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import re

st.set_page_config(page_title="OP.GG 챔피언 요약", layout="wide")

st.title("🔥 OP.GG 소환사 분석")

# --- 입력 ---
user_input = st.text_input("소환사 이름을 입력하세요", value="")

clean_input = user_input.replace("＃", "#").strip()

if not clean_input or "#" not in clean_input:
    st.info("닉네임#태그 형태로 입력해주세요. 예: Hide on bush#KR1")
    st.stop()

try:
    nickname, tag = clean_input.split("#", 1)
except ValueError:
    st.error("닉네임#태그 형태가 올바르지 않습니다.")
    st.stop()

encoded_name = f"{quote(nickname)}-{quote(tag)}"

# --- URL 구성 ---
BASE_URL = "https://op.gg/ko/lol/summoners/kr"
CHAMPIONS_URL = f"{BASE_URL}/{encoded_name}/champions"
MASTERY_URL = f"{BASE_URL}/{encoded_name}/mastery"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
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


# ----------------------------------------------------
# 🟦 1) 챔피언 통계(모스트픽) 파싱
# ----------------------------------------------------
def parse_champions(html):
    soup = BeautifulSoup(html, "html.parser")

    champs = []
    rows = soup.select("tr, div.ChampionBox, div.champion")

    valid_rows = []
    for r in rows:
        text = r.get_text(" ", strip=True)
        if "모든 챔피언" in text:
            continue
        if "vs" in text:
            continue
        if re.search(r"승|패|%", text):
            valid_rows.append(r)

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


# ----------------------------------------------------
# 🟩 2) 숙련도(Mastery) Top5 파싱
# ----------------------------------------------------
def parse_mastery(html):
    soup = BeautifulSoup(html, "html.parser")

    container = soup.find('div', attrs={"id": "content-container"})
    if not container:
        return []

    rows = container.find_all('div', attrs={"data-tooltip-id": "opgg-tooltip"})
    rows = rows[:5]  # 상위 5개만

    mastery_list = []

    for r in rows:
        # 이미지 + 이름
        img_tag = r.find("img")
        img = img_tag["src"] if img_tag else None
        name = img_tag["alt"] if img_tag and img_tag.has_attr("alt") else "Unknown"

        # 숙련도 점수
        score_tag = r.find("span", class_="mx-auto")
        score = score_tag.text.strip() if score_tag else "-"

        # 숙련도 레벨(뱃지)
        level_tag = r.find("span", class_="relative")
        badge_level = "-"
        if level_tag:
            sub = level_tag.find("span", class_="text-2xs leading-none text-white")
            if sub:
                badge_level = sub.text.strip()

        mastery_list.append({
            "img": img,
            "name": name,
            "score": score,
            "badge_level": badge_level
        })

    return mastery_list


# ----------------------------------------------------
# 🔵 실행 (챔피언 통계 + 숙련도)
# ----------------------------------------------------
with st.spinner("OP.GG에서 데이터를 불러오는 중..."):
    html_champ = fetch(CHAMPIONS_URL)
    html_mastery = fetch(MASTERY_URL)


# -------------------------
# 챔피언 통계 출력
# -------------------------
if html_champ:
    champions = parse_champions(html_champ)

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


# -------------------------
# 숙련도 출력
# -------------------------
if html_mastery:
    mastery = parse_mastery(html_mastery)

    st.markdown("---")
    st.header("🏅 숙련도 Top 5")

    for i, m in enumerate(mastery, start=1):
        cols = st.columns([1, 4])
        with cols[0]:
            if m["img"]:
                st.image(m["img"], width=70)
        with cols[1]:
            st.subheader(f"{i}. {m['name']}")
            st.write(f"✨ 숙련도 점수: **{m['score']}**")
            st.write(f"🏆 숙련도 레벨: **{m['badge_level']}**")


st.markdown("---")
st.caption(f"데이터 출처: OP.GG (챔피언: {CHAMPIONS_URL}, 숙련도: {MASTERY_URL})")
