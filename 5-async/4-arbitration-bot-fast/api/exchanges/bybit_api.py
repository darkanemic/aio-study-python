import aiohttp
from api.base_api import ExchangeAPI
from core.logger import logger
from core.utils import handle_http_error


class BybitAPI(ExchangeAPI):
    def __init__(self):
        super().__init__()
        self._base_url = "https://api.bybit.com/v5"

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()

    async def make_api_request(self, endpoint, params):
        url = f"{self._base_url}{endpoint}"
        try:
            async with self.session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientResponseError as http_error:
            logger.error(
                f"❌ HTTP ошибка при запросе к {url} - статус: {http_error.status}"
            )
            handle_http_error(http_error.status)
        except aiohttp.ClientConnectionError as error:
            logger.error(f"❌ Ошибка соединения: {error}")
        except aiohttp.ClientPayloadError as error:
            logger.error(f"❌ Ошибка обработки данных: {error}")
        except aiohttp.ClientError as error:
            logger.error(f"❌ Ошибка при запросе: {error}")
        return None

    async def request_spot_data(self):
        endpoint = "/market/tickers"
        params = {"category": "spot"}
        exchange_response = await self.make_api_request(endpoint, params)
        if exchange_response:
            logger.info("✅ Успешно получили данные SPOT рынка биржи Bybit.")
            self.spot_data = exchange_response
            return True
        return False

    async def request_ticker_data(self, ticker):
        endpoint = "/market/ticker"
        params = {"instId": ticker}
        exchange_response = await self.make_api_request(endpoint, params)
        if exchange_response and exchange_response.get("code") == "0":
            return exchange_response
        else:
            logger.error(
                f"❌ Ошибка при получении данных для тикера {ticker}: {exchange_response}"
            )
            return None

    async def get_tickers_list(self):
        if self.spot_data is None:
            logger.error("❌ Spot data is not loaded.")
            raise ValueError("Spot data is not loaded.")
        return [item["symbol"] for item in self.spot_data["result"]["list"]]

    def generate_tickers_dict(self):
        if self.spot_data is None:
            logger.error(
                "❌ Spot data is not loaded, невозможно создать словарь тикеров."
            )
            raise ValueError("Spot data is not loaded.")
        self.tickers_dict = {
            item["symbol"]: item for item in self.spot_data["result"]["list"]
        }
        return True

    def get_price_from_dict(self, ticker):
        if self.tickers_dict is None:
            self.generate_tickers_dict()
        if ticker in self.tickers_dict:
            return float(self.tickers_dict[ticker]["lastPrice"])
        else:
            logger.error(f"❌ Тикер {ticker} не найден.")
            return None

    async def get_price_from_request(self, ticker):
        request_response = await self.request_ticker_data(ticker)
        if request_response and request_response.get("data"):
            data = request_response["data"][0]
            last_price = data.get("last")
            if last_price:
                try:
                    return float(last_price)
                except ValueError:
                    logger.error(
                        f"❌ Неверный формат цены для тикера {ticker}: {last_price}"
                    )
            else:
                logger.error(f"❌ Цена отсутствует для тикера {ticker}")
        else:
            logger.error(
                f"❌ Некорректный ответ для тикера {ticker}: {request_response}"
            )
        return None
