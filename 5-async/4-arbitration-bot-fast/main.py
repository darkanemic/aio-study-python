import asyncio
from api.exchanges.okx_api import OkxAPI
from api.exchanges.binance_api import BinanceAPI
from api.exchanges.bybit_api import BybitAPI
from core.logger import logger


async def fetch_and_save_data(exchange_api, filename, exchange_name):
    await exchange_api.request_spot_data()
    if await exchange_api.save_spot_data(filename):
        logger.info(
            f"✅ SPOT данные биржи {exchange_name} успешно сохранены в {filename}."
        )
    else:
        logger.error(f"❌ Не удалось сохранить SPOT данные биржи {exchange_name}.")


async def fetch_and_save_all_exchanges(okx_api, binance_api, bybit_api):
    tasks = [
        fetch_and_save_data(okx_api, "okx_spot_data.json", "OKX"),
        fetch_and_save_data(binance_api, "binance_spot_data.json", "Binance"),
        fetch_and_save_data(bybit_api, "bybit_spot_data.json", "Bybit"),
    ]
    await asyncio.gather(*tasks)


async def find_common_tickers(okx_api, binance_api, bybit_api):
    okx_tickers_list = await okx_api.get_tickers_list()
    binance_tickers_list = await binance_api.get_tickers_list()
    bybit_tickers_list = await bybit_api.get_tickers_list()

    common_tickers = (
        set(okx_tickers_list) & set(binance_tickers_list) & set(bybit_tickers_list)
    )
    return common_tickers


async def load_and_find_common_tickers(okx_api, binance_api, bybit_api):
    tasks = [
        okx_api.load_spot_data("okx_spot_data.json"),
        binance_api.load_spot_data("binance_spot_data.json"),
        bybit_api.load_spot_data("bybit_spot_data.json"),
    ]
    await asyncio.gather(*tasks)
    common_tickers = await find_common_tickers(okx_api, binance_api, bybit_api)
    logger.info(
        f"📣 Найдено {len(common_tickers)} общих тикеров. Попробуем найти среди них лучшие сделки..."
    )
    return common_tickers


async def create_spreads_data(okx_api, binance_api, bybit_api, common_tickers):
    spreads_data = []
    for ticker in common_tickers:
        okx_price = okx_api.get_price_from_dict(ticker)
        binance_price = binance_api.get_price_from_dict(ticker)
        bybit_price = bybit_api.get_price_from_dict(ticker)

        prices = {"OKX": okx_price, "Binance": binance_price, "Bybit": bybit_price}

        max_exchange = max(prices, key=prices.get)
        min_exchange = min(prices, key=prices.get)

        hi_price = prices[max_exchange]
        lo_price = prices[min_exchange]

        ticker_blacklist = ["AUD", "TRY", "EUR"]
        price_threshold = 0.001
        if not any(currency in ticker for currency in ticker_blacklist):
            if hi_price > price_threshold and lo_price > price_threshold:
                spread_percent = ((hi_price - lo_price) / lo_price) * 100
                direction = (
                    f"{min_exchange} -> {max_exchange}"
                    if spread_percent > 0
                    else "None"
                )
                spreads_data.append(
                    {
                        "ticker": ticker,
                        "hi_price": hi_price,
                        "lo_price": lo_price,
                        "direction": direction,
                        "spread_percent": round(spread_percent, 2),
                    }
                )

    return spreads_data


def rank_spreads_data(spreads_data):
    ranked_data = sorted(spreads_data, key=lambda x: x["spread_percent"], reverse=True)
    return ranked_data


def print_line():
    print("-" * 101)


def print_profitable_tickers(spreads_data, spread_threshold):
    profitable_tickers = []
    for ticker in spreads_data:
        if (
            ticker["spread_percent"] > spread_threshold
            and ticker["direction"] != "None"
        ):
            profitable_tickers.append(ticker)
    print_line()
    print(
        f"{'№':<4} {'Пара':<12} {'Направление':<20} {'Цена покупки':<15} {'Цена продажи':<15}"
        f" {'Спред %':<10} {'Спред превышает':<15} {spread_threshold}%"
    )
    print_line()

    for index, item in enumerate(profitable_tickers, start=1):
        ticker = item["ticker"]
        buy_price = item["lo_price"]
        sell_price = item["hi_price"]
        spread_percent = item["spread_percent"]
        profitable = "✅"
        direction = item["direction"]

        # print(buy_price, sell_price, spread_procent, profitable, direction)
        print(
            f"{index:<4} {ticker:<12} {direction:<20} {buy_price:<15.4f} "
            f"{sell_price:<15.4f} {spread_percent:<10.2f} {profitable:<15}"
        )
    print_line()
    print(f"Найдено {len(profitable_tickers)} выгодных сделок.")
    print_line()


async def main():
    # значение спреда в % выше которого будет выводиться тикер
    spread_threshold = 0.5
    logger.info(
        f"🚀 Программа найдёт общие тикеры, посчитает спред и выведет тикеры со спредом выше {spread_threshold}%."
    )

    async with OkxAPI() as okx_api, BinanceAPI() as binance_api, BybitAPI() as bybit_api:
        # асинхронно получаем и сохраняем данные
        await fetch_and_save_all_exchanges(okx_api, binance_api, bybit_api)
        # асинхронно загружаем данные и находим общие тикеры
        common_tickers = await load_and_find_common_tickers(
            okx_api, binance_api, bybit_api
        )
        # создадим список спредов, отфильтруем нулевые и некоторые фиатные пары к национальным валютам
        spreads_data = await create_spreads_data(
            okx_api, binance_api, bybit_api, common_tickers
        )
        # ранжируем список от большего к меньшему
        ranked_spreads_data = rank_spreads_data(spreads_data)
        # выведем результаты в консоль
        print_profitable_tickers(ranked_spreads_data, spread_threshold)

if __name__ == "__main__":
    asyncio.run(main())
