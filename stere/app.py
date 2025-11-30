import streamlit as st
import requests
import urllib.parse
import pandas as pd

# --- 페이지 설정 ---
st.set_page_config(page_title="롤 도전과제 검색기", page_icon="🏆", layout="wide")

# --- 헤더 & 초기화 버튼 ---
col_title, col_btn = st.columns([4, 1])
with col_title:
    st.title("🏆 롤 도전과제 검색기")
with col_btn:
    if st.button("🗑️ 데이터 초기화", help="문제가 생기면 누르세요"):
        st.cache_data.clear()
        st.rerun()

# --- API 키 설정 ---
st.sidebar.header("🔑 설정")
if "API_KEY" in st.secrets:
    API_KEY = st.secrets["API_KEY"]
else:
    API_KEY = st.sidebar.text_input("API Key 입력 (RGAPI-...)", type="password")

if not API_KEY:
    st.warning("👈 왼쪽 사이드바에 API 키를 입력해주세요.")
    st.stop()

# --- 설정 ---
REGION_ACCOUNT = "asia"
REGION_KR = "kr"
HEADERS = {
    "X-Riot-Token": API_KEY,
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
}

# --- API 함수 ---

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

# --- 실행 로직 ---

with st.spinner("사전 데이터 로드 중..."):
    config_map = get_all_challenge_config()

if not config_map:
    st.error("🚨 API 키가 만료되었거나 데이터를 가져오지 못했습니다.")
    st.stop()

riot_id = st.text_input("Riot ID 입력 (예: hide on bush#KR1)", value="hide on bush#KR1")

if riot_id:
    if "#" not in riot_id:
        st.error("형식 오류: `이름#태그` 형식으로 입력해주세요.")
        st.stop()
        
    name, tag = riot_id.split('#')
    
    with st.spinner(f"🔍 {name}님의 정보를 찾는 중..."):
        puuid = get_puuid(name, tag)
        
        if not puuid:
            st.error("❌ 사용자를 찾을 수 없습니다.")
            st.stop()
            
        user_data = get_player_data(puuid)
        
        if user_data:
            st.divider()
            
            # 요약 정보
            total = user_data.get('totalPoints', {})
            
            # [수정완료] 여기에 괄호 ) 를 확실하게 닫았습니다!
            col1, col2, col3 = st.columns(3)
            
            col1.metric("총 점수", f"{total.get('current', 0):,} 점")
            col2.metric("전체 등급", f"{total.get('level', 'Unknown')}")
            col3.metric("상위 퍼센트", f"{total.get('percentile', 0) * 100:.1f}%")
            
            st.subheader("📜 상세 목록")
            
            items = []
            
            for challenge in user_data.get('challenges', []):
                c_id = challenge.get('challengeId')
                
                # Config에서 이름 찾기
                c_info = config_map.get(str(c_id))
                
                c_name = f"ID: {c_id}"
                c_desc = ""
                
                if c_info:
                    names = c_info.get('localizedNames', {})
                    ko_info = names.get('ko_KR') or names.get('en_US') or {}
                    c_name = ko_info.get('name', c_name)
                    c_desc = ko_info.get('description', '')

                # 점수 가져오기
                final_score = challenge.get('value')

                # 카테고리(0~5번) 설명 추가
                if c_id <= 5:
                    c_desc = "📊 카테고리 합산 점수" 

                lvl = challenge.get('level', 'NONE')
                
                items.append({
                    "도전과제명": c_name,
                    "등급": lvl,
                    "점수": final_score,
                    "설명": c_desc
                })
            
            if items:
                st.dataframe(
                    pd.DataFrame(items),
                    column_config={
                        "도전과제명": st.column_config.TextColumn("도전과제명", width="medium"),
                        "등급": st.column_config.TextColumn("등급", width="small"),
                        "점수": st.column_config.NumberColumn("점수/진행도", format="%.0f"),
                        "설명": st.column_config.TextColumn("설명", width="large")
                    },
                    use_container_width=True,
                    # 아이콘 컬럼 제거됨
                    column_order=("도전과제명", "등급", "점수", "설명"),
                    hide_index=True
                )
            else:
                st.info("데이터가 없습니다.")
        else:
            st.error("❌ 정보를 불러오지 못했습니다.")