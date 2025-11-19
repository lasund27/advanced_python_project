import streamlit as st
import requests
import urllib.parse
import urllib3

# 보안 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.title("🚑 긴급 진단 모드")

# 1. API 키 확인
api_key = st.secrets.get("API_KEY", "")
if not api_key:
    st.error("secrets.toml 파일에 API 키가 없습니다!")
    st.stop()

st.write(f"🔑 적용된 API 키: {api_key[:5]}... (앞자리 확인)")

# 2. 검색 테스트
summoner_name = st.text_input("소환사 이름 (태그 없이)", value="hide on bush")

if st.button("진단 시작"):
    encoded_name = urllib.parse.quote(summoner_name)
    # 한국 서버(KR)에 직접 연결 시도
    url = f"https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-name/{encoded_name}"
    
    headers = {
        "X-Riot-Token": api_key,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        with st.spinner("서버에 신호를 보내는 중..."):
            response = requests.get(url, headers=headers, verify=False, timeout=10)
            
        # 결과 출력
        st.subheader("결과 리포트")
        if response.status_code == 200:
            st.success("✅ 성공! 데이터 수신 완료")
            st.json(response.json())
        elif response.status_code == 401:
            st.error("🚫 401 오류: API 키가 틀렸거나 만료되었습니다. 키를 재발급 받으세요.")
        elif response.status_code == 403:
            st.error("🚫 403 오류: API 키 입력 실수(공백 등) 또는 권한 부족입니다.")
        elif response.status_code == 404:
            st.error(f"❓ 404 오류: '{summoner_name}'라는 소환사를 찾을 수 없습니다.")
        else:
            st.error(f"⚠️ 기타 오류 발생 (코드: {response.status_code})")
            st.write(response.text)
            
    except Exception as e:
        st.error("💥 치명적 오류 (네트워크 차단 확실함)")
        st.error(f"에러 내용: {e}")
        st.info("👉 해결책: 와이파이를 끄고, 스마트폰 핫스팟을 연결하세요.")