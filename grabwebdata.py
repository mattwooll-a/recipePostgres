import requests
from bs4 import BeautifulSoup
import time

url = "https://www.recipetineats.com/oven-baked-barbecue-pork-ribs/"
headers = {
    "User-Agent": "personalrecipecontainer/0.1 (contact: mattwooll.a@gmail.com)"
}
response = requests.get(url, headers=headers, timeout=10)
response.raise_for_status()
soup = BeautifulSoup(response.text, "html.parser")
rec_div = soup.find("div", class_="wprm-entry-content")
cal_div = soup.find("div", class_="wprm-entry-nutrition")
if not rec_div:
    print("Content not found")
else:
    text = rec_div.get_text(separator="\n", strip=True)
    print(text)

if not cal_div:
    print("Content not found")
else:
    text = cal_div.get_text(separator="\n", strip=True)
    print(text)




