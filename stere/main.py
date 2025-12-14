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
st.set_page_config(
    page_title="LOL 통합 분석 대시보드",
    page_icon="🎮",
    layout="wide"
)
st.title("🎮 LOL 통합 분석 대시보드")

# ---------------------------------------------------------------
# 사이드바 메뉴
# ---------------------------------------------------------------
menu = st.sidebar.selectbox(
    "기능 선택",
    [" 롤 도전과제 검색기 (Riot API)", " OP.GG 소환사 분석"]
)
st.sidebar.markdown("---")

# =====================================================================
# 1) 🔹 롤 도전과제 검색기 (Riot API)
# =====================================================================
if menu == " 롤 도전과제 검색기 (Riot API)":

    st.header(" 롤 도전과제 검색기 (Riot API)")

    try:
        API_KEY = st.secrets["API_KEY"]
    except KeyError:
        st.error(".streamlit/secrets.toml 파일에 API_KEY 값이 없습니다.")
        st.stop()

    REGION_ACCOUNT = "asia"
    REGION_KR = "kr"

    HEADERS = {
        "X-Riot-Token": API_KEY,
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "ko-KR"
    }

    @st.cache_data(ttl=3600)
    def get_puuid(game_name, tag_line):
        url = f"https://{REGION_ACCOUNT}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{urllib.parse.quote(game_name)}/{urllib.parse.quote(tag_line)}"
        res = requests.get(url, headers=HEADERS)
        return res.json().get("puuid") if res.status_code == 200 else None

    @st.cache_data(ttl=3600)
    def get_player_data(puuid):
        url = f"https://{REGION_KR}.api.riotgames.com/lol/challenges/v1/player-data/{puuid}"
        res = requests.get(url, headers=HEADERS)
        return res.json() if res.status_code == 200 else None

    @st.cache_data(ttl=86400)
    def get_all_challenge_config():
        url = f"https://{REGION_KR}.api.riotgames.com/lol/challenges/v1/challenges/config"
        res = requests.get(url, headers=HEADERS)
        return {str(i["id"]): i for i in res.json()} if res.status_code == 200 else None

    riot_id = st.text_input("Riot ID 입력 (예: Hide on bush#KR1)")
    if not riot_id or "#" not in riot_id:
        st.stop()

    name, tag = riot_id.split("#")
    puuid = get_puuid(name, tag)
    user_data = get_player_data(puuid)
    config_map = get_all_challenge_config()

    st.divider()
    total = user_data["totalPoints"]

    c1, c2, c3 = st.columns(3)
    c1.metric("총 점수", f"{total['current']:,}")
    c2.metric("전체 등급", total["level"])
    c3.metric("상위 퍼센트", f"{total['percentile']*100:.1f}%")

    items = []
    for ch in user_data["challenges"]:
        info = config_map.get(str(ch["challengeId"]), {})
        names = info.get("localizedNames", {}).get("ko_KR", {})
        items.append({
            "도전과제명": names.get("name", ch["challengeId"]),
            "등급": ch["level"],
            "점수": ch["value"]
        })

    st.dataframe(pd.DataFrame(items), use_container_width=True)

# =====================================================================
# 2) OP.GG 소환사 분석
# =====================================================================
else:
    st.header(" OP.GG 소환사 분석")

    user_input = st.text_input("소환사 이름 (닉네임#태그)")
    if not user_input or "#" not in user_input:
        st.stop()

    name, tag = user_input.split("#", 1)
    encoded = f"{quote(name)}-{quote(tag)}"

    BASE = "https://op.gg/ko/lol/summoners/kr"
    URL_CHAMP = f"{BASE}/{encoded}/champions"
    URL_MASTERY = f"{BASE}/{encoded}/mastery"

    HEADERS = {"User-Agent": "Mozilla/5.0"}

    def fetch(url):
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            r.raise_for_status()
            return r.text
        except:
            return None

    # -----------------------------------------------------------
    # 챔피언 파싱 (상대전적 완전 제거)
    # -----------------------------------------------------------
    def parse_champions(html):
        soup = BeautifulSoup(html, "html.parser")
        champs = []

        rows = soup.select("tr, div.ChampionBox, div.champion")

        for r in rows:
            txt = r.get_text(" ", strip=True)

            # ❌ 상대전적 제거
            if "vs" in txt.lower():
                continue

            img = r.find("img")
            if not img:
                continue

            wins = re.search(r"(\d+)\s*승", txt)
            losses = re.search(r"(\d+)\s*패", txt)

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

    # -----------------------------------------------------------
    # 숙련도 파싱
    # -----------------------------------------------------------
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

    html_champ = fetch(URL_CHAMP)
    html_mastery = fetch(URL_MASTERY)

    left, divider, right = st.columns([3, 0.15, 3])

    # =========================
    # 모스트 픽
    # =========================
    with left:
        st.subheader("🎯 모스트픽 Top 5")

        st.markdown("""
        <style>
        .bar-wrap {width:50%; height:18px; background:#ddd; border-radius:6px; display:flex;}
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
    # 숙련도
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
