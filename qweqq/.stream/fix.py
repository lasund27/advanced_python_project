import os

# ▼▼ 여기에 본인의 API 키를 붙여넣으세요 (따옴표 필수!) ▼▼
MY_KEY = "RGAPI-d3f3f0d9-c2d8-4215-9006-804137d2bc54"
# ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

# 현재 폴더(qweqq) 위치 확인
current_path = os.getcwd()
print(f"📂 현재 작업 위치: {current_path}")

# 1. .streamlit 폴더 생성
target_folder = os.path.join(current_path, ".streamlit")
os.makedirs(target_folder, exist_ok=True)

# 2. secrets.toml 파일 생성
target_file = os.path.join(target_folder, "secrets.toml")
content = f'API_KEY = "{MY_KEY}"'

with open(target_file, "w", encoding="utf-8") as f:
    f.write(content)

print("-" * 30)
print(f"✅ 성공! secrets.toml 파일이 생성되었습니다.")
print(f"파일 위치: {target_file}")
print("-" * 30)
print("이제 다시 'streamlit run app.py'를 실행해보세요!")