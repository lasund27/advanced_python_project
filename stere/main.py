import streamlit as st
import requests
import urllib.parse
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import quote
import re

# ---------------------------------------------------------------
# 기본 설정
# ---------------------------------------------------------------
st.set_page_config(page_title="LOL 통합 분석 대시보드", page_icon="🎮", layout="wide")
st.title("🎮 LOL 통합 분석 대시보드")

# ---------------------------------------------------------------
# 사이드바 메뉴
# ---------------------------------------------------------------
menu = st.sidebar.selectbox(
    "기능 선택",
    ["🔑 롤 도전과제 검색기 (Riot API)", "🔥 OP.GG 소환사 분석"]
)

st.sidebar.markdown("---")

# =====================================================================
# 1) 🔹 롤 도전과제 검색기 (Riot API)
# =====================================================================
if menu == "🔑 롤 도전과제 검색기 (Riot API)":

    st.header("🔑 롤 도전과제 검색기 (Riot API)")

    # --- API Key 자동 불러오기 ---
    try:
        API_KEY = st.secrets["API_KEY"]
    except KeyError:
        st.error("🚨 `.streamlit/secrets.toml` 파일에 API_KEY 값이 없습니다.")
        st.stop()

    REGION_ACCOUNT = "asia"
    REGION_KR = "kr"
    HEADERS = {
        "X-Riot-Token": API_KEY,
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    # -----------------------------------------------------------
    # Riot API 함수
    # -----------------------------------------------------------
    @st.cache_data(ttl=3600)
    def get_puuid(game_name, tag_line):
        url = f"https://{REGION_ACCOUNT}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{urllib.parse.quote(game_name)}/{urllib.parse.quote(tag_line)}"
        try:
            res = requests.get(url, headers=HEADERS)
            return res.json().get("puuid") if res.status_code == 200 else None
        except:
            return None

    @st.cache_data(ttl=3600)
    def get_player_data(puuid):
        url = f"https://{REGION_KR}.api.riotgames.com/lol/challenges/v1/player-data/{puuid}"
        try:
            res = requests.get(url, headers=HEADERS)
            return res.json() if res.status_code == 200 else None
        except:
            return None

    @st.cache_data(ttl=86400)
    def get_all_challenge_config():
        url = f"https://{REGION_KR}.api.riotgames.com/lol/challenges/v1/challenges/config"
        try:
            res = requests.get(url, headers=HEADERS)
            if res.status_code == 200:
                data = res.json()
                return {str(item["id"]): item for item in data}
            return None
        except:
            return None

    # -----------------------------------------------------------
    # Config 미리 로드
    # -----------------------------------------------------------
    with st.spinner("도전과제 정보를 불러오는 중..."):
        config_map = get_all_challenge_config()

    if not config_map:
        st.error("🚨 API 키가 잘못되었거나 데이터를 불러오지 못했습니다.")
        st.stop()

    # -----------------------------------------------------------
    # Riot ID 입력
    # -----------------------------------------------------------
    riot_id = st.text_input("Riot ID 입력 (예: Hide on bush#KR1)")

    if not riot_id:
        st.stop()

    if "#" not in riot_id:
        st.error("❌ `이름#태그` 형식으로 입력해주세요.")
        st.stop()

    name, tag = riot_id.split("#")

    with st.spinner(f"🔍 {name}님의 데이터를 조회 중..."):
        puuid = get_puuid(name, tag)

    if not puuid:
        st.error("❌ 소환사를 찾을 수 없습니다.")
        st.stop()

    user_data = get_player_data(puuid)

    if not user_data:
        st.error("❌ 정보를 불러오지 못했습니다.")
        st.stop()

    # -----------------------------------------------------------
    # 요약 정보
    # -----------------------------------------------------------
    st.divider()
    total = user_data.get("totalPoints", {})
    col1, col2, col3 = st.columns(3)
    col1.metric("총 점수", f"{total.get('current', 0):,} 점")
    col2.metric("전체 등급", total.get("level", "Unknown"))
    col3.metric("상위 퍼센트", f"{total.get('percentile', 0)*100:.1f}%")

    st.subheader("📜 상세 목록")

    items = []
    for challenge in user_data.get("challenges", []):
        c_id = challenge.get("challengeId")
        c_info = config_map.get(str(c_id), {})

        names = c_info.get("localizedNames", {})
        ko = names.get("ko_KR") or names.get("en_US") or {}
        c_name = ko.get("name", f"ID: {c_id}")
        c_desc = ko.get("description", "")

        if c_id <= 5:
            c_desc = "📊 카테고리 합산 점수"

        items.append({
            "도전과제명": c_name,
            "등급": challenge.get("level", "NONE"),
            "점수": challenge.get("value"),
            "설명": c_desc
        })

    st.dataframe(
        pd.DataFrame(items),
        use_container_width=True,
        hide_index=True
    )

# =====================================================================
# 2) 🔥 OP.GG 소환사 분석
# =====================================================================
elif menu == "🔥 OP.GG 소환사 분석":

    st.header("🔥 OP.GG 소환사 분석")

    user_input = st.text_input("소환사 이름을 입력하세요 (예: Hide on bush#KR1)")

    clean_input = user_input.replace("＃", "#").strip()

    if not clean_input or "#" not in clean_input:
        st.info("닉네임#태그 형태로 입력해주세요.")
        st.stop()

    nickname, tag = clean_input.split("#", 1)
    encoded = f"{quote(nickname)}-{quote(tag)}"

    BASE = "https://op.gg/ko/lol/summoners/kr"
    URL_CHAMP = f"{BASE}/{encoded}/champions"
    URL_MASTERY = f"{BASE}/{encoded}/mastery"

    HEADERS = {"User-Agent": "Mozilla/5.0"}

    # -----------------------------------------------------------
    # HTML 요청
    # -----------------------------------------------------------
    def fetch(url):
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            res.raise_for_status()
            return res.text
        except Exception as e:
            st.error(f"페이지 요청 실패: {e}")
            return None

    # -----------------------------------------------------------
    # 챔피언 정보 파싱
    # -----------------------------------------------------------
    def parse_champions(html):
        soup = BeautifulSoup(html, "html.parser")
        champs = []

        rows = soup.select("tr, div.ChampionBox, div.champion")
        valid = []

        for r in rows:
            txt = r.get_text(" ", strip=True)
            if "모든 챔피언" in txt: continue
            if "vs" in txt: continue
            if re.search(r"승|패|%", txt):
                valid.append(r)

        valid = valid[:5]

        for r in valid:
            img_tag = r.select_one("img[src*='champion']")
            img = img_tag.get("src") if img_tag else None
            name = img_tag.get("alt") if img_tag else "Unknown"

            txt = r.get_text(" ", strip=True)
            winrate = re.search(r"(\d{1,3}\.?\d*)%", txt)
            wins = re.search(r"(\d+)\s*승", txt)
            losses = re.search(r"(\d+)\s*패", txt)

            champs.append({
                "img": img,
                "name": name,
                "winrate": winrate.group(1) + "%" if winrate else "-",
                "wins": wins.group(1) if wins else "-",
                "losses": losses.group(1) if losses else "-"
            })

        return champs

    # -----------------------------------------------------------
    # 숙련도 정보 파싱
    # -----------------------------------------------------------
    def parse_mastery(html):
        soup = BeautifulSoup(html, "html.parser")
        container = soup.find("div", {"id": "content-container"})
        if not container:
            return []

        rows = container.find_all("div", {"data-tooltip-id": "opgg-tooltip"})[:5]
        result = []

        for r in rows:
            img_tag = r.find("img")
            img = img_tag.get("src") if img_tag else None
            name = img_tag.get("alt") if img_tag else "Unknown"

            score = r.find("span", class_="mx-auto")
            score_val = score.text.strip() if score else "-"

            level_tag = r.find("span", class_="relative")
            badge = "-"
            if level_tag:
                sub = level_tag.find("span", class_="text-2xs")
                if sub:
                    badge = sub.text.strip()

            result.append({
                "img": img,
                "name": name,
                "score": score_val,
                "badge_level": badge
            })

        return result

    # -----------------------------------------------------------
    # 데이터 요청
    # -----------------------------------------------------------
    with st.spinner("OP.GG 데이터를 불러오는 중..."):
        html_champ = fetch(URL_CHAMP)
        html_mastery = fetch(URL_MASTERY)

    # -----------------------------------------------------------
    # 챔피언 Top5 출력
    # -----------------------------------------------------------
    if html_champ:
        st.subheader("🎯 모스트픽 챔피언 Top 5")

        for i, c in enumerate(parse_champions(html_champ), start=1):
            cols = st.columns([1, 4])
            with cols[0]:
                if c["img"]:
                    st.image(c["img"], width=70)
            with cols[1]:
                st.write(f"### {i}. {c['name']}")
                st.write(f"승률: **{c['winrate']}**")
                st.write(f"승리: {c['wins']}회 / 패배: {c['losses']}회")

    # -----------------------------------------------------------
    # 숙련도 Top5 출력
    # -----------------------------------------------------------
    if html_mastery:
        st.markdown("---")
        st.subheader("🏅 숙련도 Top 5")

        for i, m in enumerate(parse_mastery(html_mastery), start=1):
            cols = st.columns([1, 4])
            with cols[0]:
                if m["img"]:
                    st.image(m["img"], width=70)
            with cols[1]:
                st.write(f"### {i}. {m['name']}")
                st.write(f"✨ 숙련도 점수: **{m['score']}**")
                st.write(f"🏆 숙련도 레벨: **{m['badge_level']}**")
