import streamlit as st
import requests
import urllib.parse
import pandas as pd
import os

# --- (전역) 설정 ---
# secrets.toml에서 API 키 가져오기
API_KEY = st.secrets.get("API_KEY", "")

# 서버 주소 설정
REGION_API = "asia"      # 계정 검색용 (PUUID)
REGION_PLATFORM = "kr"   # 도전과제/랭크/숙련도용

# API 요청 헤더 (User-Agent 포함)
HEADERS = {
    "X-Riot-Token": API_KEY,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
}

# --- API 및 데이터 로드 함수들 ---

@st.cache_data
def load_challenge_names():
    """lol_challenges.csv 파일을 읽어서 ID:이름 딕셔너리로 반환"""
    csv_file = "lol_challenges.csv"
    if not os.path.exists(csv_file):
        return {}
    
    try:
        # CSV 파일 로드 (id, name 컬럼이 있다고 가정)
        df = pd.read_csv(csv_file)
        # 딕셔너리 형태로 변환 {10100006: 'ARAM God', ...} 
        return dict(zip(df['id'], df['name']))
    except Exception as e:
        st.error(f"CSV 로드 중 오류 발생: {e}")
        return {}

@st.cache_data(ttl=3600)
def get_puuid(game_name, tag_line):
    if not API_KEY: return None
    encoded_name = urllib.parse.quote(game_name)
    encoded_tag = urllib.parse.quote(tag_line)
    url = f"https://{REGION_API}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{encoded_name}/{encoded_tag}"
    
    try:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            return response.json()['puuid']
        return None
    except:
        return None

@st.cache_data(ttl=3600)
def get_challenge_data(puuid):
    if not API_KEY: return None
    url = f"https://{REGION_PLATFORM}.api.riotgames.com/lol/challenges/v1/player-data/{puuid}"
    try:
        response = requests.get(url, headers=HEADERS)
        return response.json() if response.status_code == 200 else None
    except: return None

# --- 화면 구성 (GUI) ---

st.set_page_config(page_title="롤 전적 검색", page_icon="🎮")

st.sidebar.title("🎮 롤 전적 검색기")
st.sidebar.caption("팀원: 이주현, 황보현준")

# API 키 확인
if not API_KEY:
    st.error("⚠️ API 키가 없습니다! `secrets.toml` 파일을 확인하세요.")
    st.stop()

# 메뉴 선택
menu = st.sidebar.radio("메뉴 선택", ["🏆 도전과제"])

# 검색창
riot_id = st.text_input("Riot ID 입력 (이름#태그)", value="hide on bush#KR1")

if riot_id:
    try:
        if "#" not in riot_id:
            st.warning("형식이 틀렸습니다. `이름#태그` 형식으로 입력하세요.")
            st.stop()
            
        game_name, tag_line = riot_id.split('#')
        
        with st.spinner("데이터 조회 중..."):
            # 1. PUUID 조회
            puuid = get_puuid(game_name, tag_line)
            
            if not puuid:
                st.error("❌ 소환사를 찾을 수 없습니다. (키 만료 또는 오타)")
                st.stop()

            # --- 🏆 도전과제 페이지 ---
            if menu == "🏆 도전과제":
                st.title(f"🏆 {game_name}님의 도전과제")
                
                # 도전과제 데이터 API 호출
                challenges = get_challenge_data(puuid)
                # CSV에서 이름 매핑 데이터 로드 (추가된 부분)
                challenge_name_map = load_challenge_names()
                
                if challenges:
                    total = challenges.get('totalPoints', {})
                    st.metric("총 점수", f"{total.get('current', 0):,} 점", f"등급: {total.get('level', 'Unknown')}")
                    st.divider()
                    st.subheader("📜 상세 목록")
                    
                    items = []
                    base_url = "https://ddragon.leagueoflegends.com/cdn/img/challenges-images/"
                    
                    for c in challenges.get('challenges', []):
                        lvl = c.get('level', 'NONE')
                        c_id = c.get('challengeId')
                        
                        # 아이콘 URL 처리
                        icon_url = f"{base_url}{lvl.lower()}.png" if lvl != 'NONE' else ""
                        
                        # ID를 이름으로 변환 (없으면 ID 그대로 표시)
                        c_name = challenge_name_map.get(c_id, f"Unknown ID ({c_id})")

                        items.append({
                            "아이콘": icon_url,
                            "도전과제명": c_name,  # ID 대신 이름 사용
                            "등급": lvl,
                            "점수": c.get('current')
                        })
                    
                    if items:
                        # 데이터프레임 생성
                        df_items = pd.DataFrame(items)
                        
                        st.dataframe(
                            df_items,
                            column_config={
                                "아이콘": st.column_config.ImageColumn("등급", width="small"),
                                "도전과제명": st.column_config.TextColumn("도전과제명"),
                                "점수": st.column_config.NumberColumn("점수", format="%d")
                            },
                            use_container_width=True,
                            column_order=("아이콘", "도전과제명", "등급", "점수"), # 순서 변경
                            hide_index=True
                        )
                    else:
                        st.info("달성한 도전과제가 없습니다.")
                else:
                    st.error("❌ 도전과제 정보를 불러올 수 없습니다.")

    except Exception as e:
        st.error(f"오류 발생: {e}")