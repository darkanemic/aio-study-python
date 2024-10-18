import requests


def clean_string(s):
    cleaned = ''.join(char for char in s if char.isalpha())
    return cleaned


def handle_http_error(http_error):
    status_code = http_error.response.status_code if http_error.response else None
    if status_code == 400:
        print("Ошибка 400: Неверный запрос. Проверьте корректность параметров запроса.")
    elif status_code == 401:
        print("Ошибка 401: Неавторизованный доступ. Проверьте токен или учетные данные.")
    elif status_code == 404:
        print("Ошибка 404: Ресурс не найден. Проверьте правильность URL.")
    elif status_code == 429:
        print("Ошибка 429: Превышено количество запросов. Попробуйте снова позже или используйте прокси.")
    elif status_code == 500:
        print("Ошибка 500: Внутренняя ошибка сервера. Попробуйте снова позже.")
    elif status_code == 502:
        print("Ошибка 502: Неверный ответ шлюза. Возможно, сервер перегружен.")
    elif status_code == 503:
        print("Ошибка 503: Сервис временно недоступен. Сервер перегружен или на обслуживании.")
    else:
        print(f"Произошла HTTP ошибка с кодом {status_code}.")


def fetch_exchange_data(exchange_api_url):
    response = requests.get(exchange_api_url)
    try:
        response.raise_for_status()
        data = response.json()
        if data:
            print(f'Ответ на запрос {exchange_api_url} получен.')
        else:
            print('Ответ от сервера пуст.')
    except requests.exceptions.HTTPError as http_error:
        handle_http_error(http_error)
    except requests.exceptions.ConnectionError as error:
        print(f'Ошибка соединения: {error}')
    except requests.exceptions.Timeout as error:
        print(f'Превышено время ожидания: {error}')
    except requests.exceptions.RequestException as error:
        print(f'Произошла ошибка при попытке запроса: {error}')
    return data


def calculate_spreads(kucoin_exchange_data, binance_exchange_data):
    spreads_data = []
    for kucoin_pair in kucoin_exchange_data['data']['ticker']:
        for binance_pair in binance_exchange_data:
            if clean_string(kucoin_pair['symbol']) == binance_pair['symbol']:  # Найдены пары на обейх биржах
                spread = float(kucoin_pair['last']) - float(binance_pair['price'])
                quote_currency = kucoin_pair['symbol'].split('-')
                spread_usd = spread * float(kucoin_prices_data['data'][quote_currency[1]])
                kucoin_price = float(kucoin_pair['last']) * float(kucoin_prices_data['data'][quote_currency[1]])
                binance_price = float(binance_pair['price']) * float(kucoin_prices_data['data'][quote_currency[1]])
                if spread > 0:
                    direction = 'Binance>Kucoin'
                elif spread < 0:
                    direction = 'Kucoin>Binance'
                else:
                    direction = 'Цены на биржах равны'
                spreads_data.append({
                    'kucoin_ticker': kucoin_pair['symbol'],
                    'binance_ticker': binance_pair['symbol'],
                    'kucoin_price': kucoin_price,
                    'binance_price': binance_price,
                    'spread_usd': spread_usd,
                    'direction': direction
                })
    return spreads_data


def spreads_data_ranking(spreads_data):
    ranked_data = sorted(spreads_data, key=lambda x: x['spread_usd'], reverse=True)
    return ranked_data


def display_top_ten_spreads(spreads_to_display):
    top_10 = spreads_to_display[:10]
    print("-" * 80)
    print("Вот 10 самых выгодных пар для арбитража между биржами Binance и Kucoin.")
    print("-" * 80)
    print(f"{'№':<4} {'Пара':<12} {'Направление':<20} {'Цена покупки $':<15} {'Цена продажи $':<15} {'Профит $':<10}")
    print("-" * 80)

    for index, item in enumerate(top_10, start=1):
        if item['direction'] == 'Binance>Kucoin':
            buy_price = item['binance_price']
            sell_price = item['kucoin_price']
        else:
            buy_price = item['kucoin_price']
            sell_price = item['binance_price']

        print(
            f"{index:<4} {item['kucoin_ticker']:<12} {item['direction']:<20} {buy_price:<15.2f} "
            f"{sell_price:<15.2f} {item['spread_usd']:<10.2f}")
    print("-" * 80)
    print(f'Всего сравнили {len(spreads_to_display)} торговых пар.')
    print("-" * 80)


kucoin_tickers_url = "https://api.kucoin.com/api/v1/market/allTickers"
kucoin_prices_url = "https://api.kucoin.com/api/v1/prices"
binance_tickers_url = "https://api.binance.com/api/v3/ticker/price"

kucoin_data = fetch_exchange_data(kucoin_tickers_url)
kucoin_prices_data = fetch_exchange_data(kucoin_prices_url)
binance_data = fetch_exchange_data(binance_tickers_url)

exchanges_spreads = calculate_spreads(kucoin_data, binance_data)
ranked_spreads = spreads_data_ranking(exchanges_spreads)
display_top_ten_spreads(ranked_spreads)
