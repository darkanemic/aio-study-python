import requests
import json
import time


def handle_http_error(http_error):
    status_code = http_error.response.status_code if http_error.response else None
    if status_code == 400:
        print("Ошибка 400: Неверный запрос. Проверьте корректность параметров запроса.")
    elif status_code == 401:
        print(
            "Ошибка 401: Неавторизованный доступ. Проверьте токен или учетные данные."
        )
    elif status_code == 404:
        print("Ошибка 404: Ресурс не найден. Проверьте правильность URL.")
    elif status_code == 429:
        print(
            "Ошибка 429: Превышено количество запросов. Попробуйте снова позже или используйте прокси."
        )
    elif status_code == 500:
        print("Ошибка 500: Внутренняя ошибка сервера. Попробуйте снова позже.")
    elif status_code == 502:
        print("Ошибка 502: Неверный ответ шлюза. Возможно, сервер перегружен.")
    elif status_code == 503:
        print(
            "Ошибка 503: Сервис временно недоступен. Сервер перегружен или на обслуживании."
        )
    else:
        print(f"Произошла HTTP ошибка с кодом {status_code}.")


def fetch_exchange_data(exchange_api_url):
    try:
        response = requests.get(exchange_api_url)
        response.raise_for_status()
        data = response.json()
        if data:
            print(f"Ответ на запрос {exchange_api_url} получен.")
            return data
        else:
            print("Ответ от сервера пуст.")
            return None
    except requests.exceptions.HTTPError as http_error:
        handle_http_error(http_error)
    except requests.exceptions.ConnectionError as error:
        print(f"Ошибка соединения: {error}")
    except requests.exceptions.Timeout as error:
        print(f"Превышено время ожидания: {error}")
    except requests.exceptions.RequestException as error:
        print(f"Произошла ошибка при попытке запроса: {error}")
    return None


def dump_json_to_file(json_data, filename, message):
    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(json_data, file, ensure_ascii=False, indent=4)
            if message:
                print(message)
    except OSError as error:
        print(
            f"Ошибка {error} при записи файла {filename}. Возможно не хватает прав доступа. Программа завершена."
        )
        exit()


def load_json_from_file(filename):
    try:
        with open(filename, "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        print(
            f"Файл {filename} по указанному пути не найден. Пожалуйста, проверьте путь и права доступа, затем запустите заново."
        )
        exit()
    else:
        print(f"Файл {filename} найден и загружен успешно!")
    return data


def normalize_symbol(symbol):
    return symbol.replace("-", "").upper()


def calculate_spreads(kucoin_exchange_data, binance_exchange_data, kucoin_prices_data):
    spreads_data = []
    kucoin_tickers = {
        normalize_symbol(pair["symbol"]): pair
        for pair in kucoin_exchange_data["data"]["ticker"]
    }
    binance_tickers = {pair["symbol"].upper(): pair for pair in binance_exchange_data}

    # Находим общие тикеры
    common_tickers = set(kucoin_tickers.keys()) & set(binance_tickers.keys())

    for symbol in common_tickers:
        kucoin_pair = kucoin_tickers[symbol]
        binance_pair = binance_tickers[symbol]
        base_currency, quote_currency = kucoin_pair["symbol"].split("-")

        # Получаем цены котируемой валюты
        quote_currency_price = kucoin_prices_data["data"].get(quote_currency)
        if quote_currency_price is None:
            print(
                f"Не удалось найти котировку {quote_currency}. Торговая пара {symbol} не будет обработана."
            )
            continue

        # Преобразуем цены в USD
        try:
            kucoin_price = float(kucoin_pair["last"]) * float(quote_currency_price)
            binance_price = float(binance_pair["price"]) * float(quote_currency_price)
        except ValueError:
            print(
                f"Не удалось получить цену в долларах для торговой пары {symbol}. Она не будет обработана."
            )
            continue

        # Рассчитываем спред и направление
        spread = kucoin_price - binance_price
        spread_usd = abs(spread)

        if spread > 0:
            direction = "Binance>Kucoin"
        elif spread < 0:
            direction = "Kucoin>Binance"
        else:
            direction = "Цены на биржах равны"

        # if symbol == 'BULLUSDT':
        #     print(kucoin_price, binance_price, spread_usd)
        #     time.sleep(20)

        spreads_data.append(
            {
                "kucoin_ticker": kucoin_pair["symbol"],
                "binance_ticker": binance_pair["symbol"],
                "kucoin_price": kucoin_price,
                "binance_price": binance_price,
                "spread_usd": spread_usd,
                "direction": direction,
            }
        )

    return spreads_data


def spreads_data_ranking(spreads_data):
    ranked_data = sorted(spreads_data, key=lambda x: x["spread_usd"], reverse=True)
    return ranked_data


def print_line():
    print("-" * 101)


def display_top_spreads(spreads_to_display, my_spread_threshold, num_top_pairs):
    top_pairs = spreads_to_display[:num_top_pairs]
    profitable_pairs = 0
    print_line()
    print("Вот 30 пар с самым большим спредом между биржами Binance и Kucoin.")
    print_line()
    print(
        f"{'№':<4} {'Пара':<12} {'Направление':<20} {'Цена покупки$':<15} {'Цена продажи$':<15}"
        f" {'Профит$':<10} {'Спред превышает':<15} {my_spread_threshold}$"
    )
    print_line()

    for index, item in enumerate(top_pairs, start=1):
        if item["direction"] == "Binance>Kucoin":
            buy_price = item["binance_price"]
            sell_price = item["kucoin_price"]
        else:
            buy_price = item["kucoin_price"]
            sell_price = item["binance_price"]
        if item["spread_usd"] > my_spread_threshold:
            profitable = "✅"
            profitable_pairs += 1
        else:
            profitable = "❌"

        print(
            f"{index:<4} {item['kucoin_ticker']:<12} {item['direction']:<20} {buy_price:<15.2f} "
            f"{sell_price:<15.2f} {item['spread_usd']:<10.2f} {profitable:<15}"
        )
    print_line()
    print(
        f"Всего сравнили {len(spreads_to_display)} торговых пар. Найдено {profitable_pairs} выгодных сделок."
    )
    print_line()


def main(spread_threshold, numbers_of_pairs):
    #  Получим данные бирж.
    kucoin_tickers_url = "https://api.kucoin.com/api/v1/market/allTickers"
    kucoin_prices_url = "https://api.kucoin.com/api/v1/prices"
    binance_tickers_url = "https://api.binance.com/api/v3/ticker/price"

    kucoin_json = fetch_exchange_data(kucoin_tickers_url)
    kucoin_fiat_prices_json = fetch_exchange_data(kucoin_prices_url)
    binance_json = fetch_exchange_data(binance_tickers_url)
    if not kucoin_json or not kucoin_fiat_prices_json or not binance_json:
        print("Не удалось получить данные с бирж. Программа будет завершена.")
        exit()

    #  Сохранение в файл/загрузка из файла.
    dump_json_to_file(
        kucoin_json,
        "kucoin_prices.json",
        "Данные цен по парам биржи Kucoin сохранены в файл kucoin_prices.json",
    )
    dump_json_to_file(
        kucoin_fiat_prices_json,
        "kucoin_fiat_prices.json",
        "Данные фиатных цен по парам биржи Kucoin сохранены в файл kucoin_fiat_prices.json",
    )
    dump_json_to_file(
        binance_json,
        "binance_prices.json",
        "Данные цен по парам биржи Binance сохранены в файл binance_prices.json",
    )

    kucoin_data = load_json_from_file("kucoin_prices.json")
    kucoin_prices = load_json_from_file("kucoin_fiat_prices.json")
    binance_data = load_json_from_file("binance_prices.json")

    # Расчет спредов > ранжирование спредов > вывод топа пар для спреда.
    exchanges_spreads = calculate_spreads(kucoin_data, binance_data, kucoin_prices)
    ranked_spreads = spreads_data_ranking(exchanges_spreads)
    display_top_spreads(ranked_spreads, spread_threshold, numbers_of_pairs)


if __name__ == "__main__":

    current_spread_threshold = (
        10  # Порог спреда в $, после которого арбитраж становится интересным.
    )
    number_of_pairs_in_top = 30  # Количество торговых пар в топе.

    main(current_spread_threshold, number_of_pairs_in_top)
