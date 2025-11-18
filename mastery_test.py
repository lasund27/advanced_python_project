import requests
from bs4 import BeautifulSoup

url = "https://op.gg/ko/lol/summoners/kr/Hide%20on%20bush-KR1/mastery"


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122 Safari/537.36"
}

res = requests.get(url, headers=headers)

soup = BeautifulSoup(res.text, "html.parser")

for i in soup.find('div', attrs={"id":"content-container"}).find_all('div', attrs={"data-tooltip-id":"opgg-tooltip"}):
    print(i.find('img')['alt'])
    print(i.find('span', class_="mx-auto").text)
    print(i.find('span', class_="relative").find('span', attrs={'class':'text-2xs leading-none text-white'}).text)

