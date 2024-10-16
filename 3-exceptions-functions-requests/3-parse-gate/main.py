import requests

host = 'https://api.gateio.ws'
prefix = "/api/v4"
headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

url = '/spot/order_book'
query_param = ('currency_pair=BTC_USDT', 'currency_pair=BTC_USDT', 'currency_pair=BTC_USDT')
for currency_pair in query_param:
    try:
        response = requests.request('GET', host + prefix + url + '?' + currency_pair, headers=headers)
        response.raise_for_status()
        print(response.json())
    except requests.exceptions.HTTPError as error:
        print(f'HTTP ошибка: {error}')
    except requests.exceptions.ConnectionError as error:
        print(f'Ошибка соединения: {error}')
    except requests.exceptions.Timeout as error:
        print(f'Превышено время ожидания: {error}')
    except requests.exceptions.RequestException as error:
        print(f'Произошла ошибка при попытке запроса: {error}')

