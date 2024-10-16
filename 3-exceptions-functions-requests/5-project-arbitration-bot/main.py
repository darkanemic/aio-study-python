import requests

SYMBOL = "BTC-USDT"

url = f"https://api.kucoin.com/api/v1/market/allTickers"
response = requests.get(url)
r = response.json()

for token in r["data"]["ticker"]:
    symbol = token["symbol"]
    price = token["last"]
    if symbol == SYMBOL:
        print(price)
