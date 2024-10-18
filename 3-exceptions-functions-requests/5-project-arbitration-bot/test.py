import requests


def fetch_exchange_data(exchange_api_url):
    response = requests.get(url)
    r = response.json()
    return r


urlz = f"https://api.kucoin.com/api/v1/prices"
kucoin_tickers_prices = fetch_exchange_data(urlz)
print(kucoin_tickers_prices)