from abc import ABC, abstractmethod
import json
import time
import random
import asyncio
import aiohttp
import aiofiles


class ExchangeAPIError(Exception):
    """Базовый класс для ошибок API"""

    pass


class SpotDataNotLoadedError(ExchangeAPIError):
    def __init__(self, message="Spot data is not loaded."):
        super().__init__(message)


class TickerNotFoundError(ExchangeAPIError):
    def __init__(self, ticker, message="Ticker not found in the dictionary."):
        super().__init__(f"{message} Ticker: {ticker}")


class HTTPError(ExchangeAPIError):
    """Класс для обработки HTTP ошибок с автоматическим выбором сообщения"""

    def __init__(self, status_code):
        self.status_code = status_code
        self.message = self.get_error_message(status_code)
        super().__init__(self.message)

    @staticmethod
    def get_error_message(status_code):
        errors = {
            400: "❌ Ошибка 400: Неверный запрос. Проверьте корректность параметров запроса.",
            401: "❌ Ошибка 401: Неавторизованный доступ. Проверьте токен или учетные данные.",
            404: "❌ Ошибка 404: Ресурс не найден. Проверьте правильность URL.",
            429: "❌ Ошибка 429: Превышено количество запросов. Попробуйте уменьшить частоту запросов.",
            500: "❌ Ошибка 500: Внутренняя ошибка сервера. Попробуйте снова позже.",
            502: "❌ Ошибка 502: Неверный ответ шлюза. Возможно, сервер перегружен.",
            503: "❌ Ошибка 503: Сервис временно недоступен. Сервер перегружен или на обслуживании.",
        }
        return errors.get(status_code, f"Произошла HTTP ошибка с кодом {status_code}.")


class ExchangeAPI(ABC):
    def __init__(self):
        self.base_url = None
        self.spot_data = None
        self.tickers_list = None
        self.tickers_dict = None
        self.session = None

    @abstractmethod
    async def make_api_request(self, endpoint, params):
        """Отправка запроса к API биржи"""

    @abstractmethod
    async def request_spot_data(self):
        """Запрос данных всего SPOT рынка"""
        pass

    @abstractmethod
    async def request_ticker_data(self, ticker):
        """Запрос данных по отдельному тикеру"""
        pass

    @abstractmethod
    async def get_tickers_list(self):
        """Получение списка тикеров из данных SPOT"""
        pass

    @abstractmethod
    async def save_spot_data(self, filename):
        """Сохранение SPOT данных в файл"""
        pass

    @abstractmethod
    def generate_tickers_dict(self):
        """Создание словаря тикеров из данных SPOT (для быстрого получения данных для любого тикера)"""
        pass

    @abstractmethod
    def get_price_from_dict(self, ticker):
        """Получение цены тикера из словаря"""
        pass

    @abstractmethod
    async def get_price_from_request(self, ticker):
        """Получение цены тикера через отдельный запрос"""
        pass

    def reset_api_data(self):
        """Сброс API-данных"""
        self.spot_data = None
        self.tickers_list = None
        self.tickers_dict = None


class OkxAPI(ExchangeAPI):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.okx.com/api/v5"

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()

    async def make_api_request(self, endpoint, params):
        url = f"{self.base_url}{endpoint}"
        try:
            async with self.session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientResponseError as http_error:
            raise HTTPError(http_error.status)
        except aiohttp.ClientError as error:
            print(f"❌ Ошибка запроса: {error}")
            raise ExchangeAPIError(f"Ошибка запроса: {error}") from error

    async def request_spot_data(self):
        endpoint = "/market/tickers"
        params = {"instType": "SPOT"}
        try:
            exchange_response = await self.make_api_request(endpoint, params)
            if exchange_response and exchange_response.get("code") == "0":
                self.spot_data = exchange_response
                return True
            else:
                raise ExchangeAPIError("Failed to retrieve SPOT data.")
        except ExchangeAPIError as e:
            print(f"❌ Ошибка при загрузке данных SPOT: {e}")
            return False

    async def get_tickers_list(self):
        if self.spot_data is None:
            print("🔄 SPOT данные отсутствуют. Попытка загрузки...")
            if not await self.request_spot_data():
                raise SpotDataNotLoadedError()
        return [item["instId"] for item in self.spot_data["data"]]

    async def save_spot_data(self, filename):
        if self.spot_data is None:
            if not await self.request_spot_data():
                print(
                    "❌ Невозможно сохранить SPOT данные, так как загрузка не удалась."
                )
                return False
        try:
            dump_data = await dump_json_to_file(self.spot_data, filename)
            if dump_data is not True:
                raise ExchangeAPIError("Failed to save spot data.")
            return True
        except Exception as e:
            print(f"❌ Ошибка при сохранении данных SPOT: {e}")
            return False

    def generate_tickers_dict(self):
        if self.spot_data is None:
            print("🔄 SPOT данные отсутствуют. Попытка загрузки...")
            if not self.request_spot_data():
                raise SpotDataNotLoadedError()
        self.tickers_dict = {item["instId"]: item for item in self.spot_data["data"]}
        return True

    def get_price_from_dict(self, ticker):
        if self.tickers_dict is None:
            self.generate_tickers_dict()
        if ticker in self.tickers_dict:
            return float(self.tickers_dict[ticker]["last"])
        raise TickerNotFoundError(ticker)

    async def get_price_from_request(self, ticker):
        try:
            request_response = await self.request_ticker_data(ticker)
            if request_response and request_response.get("data"):
                data = request_response["data"][0]
                last_price = data.get("last")
                if last_price:
                    try:
                        return float(last_price)
                    except ValueError:
                        raise ExchangeAPIError(
                            f"Invalid price format for ticker {ticker}: {last_price}"
                        )
                raise ExchangeAPIError(f"No price found for ticker {ticker}")
            raise ExchangeAPIError(
                f"Invalid response for ticker {ticker}: {request_response}"
            )
        except ExchangeAPIError as e:
            print(f"❌ Ошибка при запросе цены для тикера {ticker}: {e}")
            return None


async def dump_json_to_file(json_data, filename):
    try:
        async with aiofiles.open(filename, "w", encoding="utf-8") as file:
            await file.write(json.dumps(json_data, ensure_ascii=False, indent=4))
            return True
    except FileNotFoundError:
        print(f"❌ Файл '{filename}' не найден. Проверьте путь.")
    except (OSError, IOError) as e:
        print(f"❌ Ошибка ввода/вывода при сохранении файла '{filename}': {e}")
    except Exception as error:
        print(f"❌ Общая ошибка при сохранении JSON: {error}")
    return False


# Вспомогательные функции и main функция запуска программы


def generate_random_tickers_list(all_tickers_list, number_of_tickers):
    return random.sample(all_tickers_list, number_of_tickers)


async def measure_time_async(func, *args, **kwargs):
    start_time = time.perf_counter()
    result = await func(*args, **kwargs)
    end_time = time.perf_counter()
    return end_time - start_time, result


async def one_request_algorithm(api, tickers_list):
    await api.request_spot_data()
    api.generate_tickers_dict()

    prices = []
    all_prices_retrieved = True

    for ticker in tickers_list:
        try:
            price = api.get_price_from_dict(ticker)
            prices.append(price)
        except TickerNotFoundError:
            print(f"❌ Тикер {ticker} не найден.")
            all_prices_retrieved = False

    total_price = sum(prices) if prices else 0
    return total_price, all_prices_retrieved


async def many_requests_algorithm(api, tickers_list, request_frequency):
    semaphore = asyncio.Semaphore(request_frequency)
    delay = 1 / request_frequency

    tasks = [
        get_price_limited(api, ticker, semaphore, delay) for ticker in tickers_list
    ]
    prices = await asyncio.gather(*tasks, return_exceptions=True)

    valid_prices = []
    all_prices_retrieved = True

    for price in prices:
        if isinstance(price, Exception):
            print(f"❌ Ошибка при получении цены: {price}")
            all_prices_retrieved = False
        elif price is not None:
            valid_prices.append(price)

    total_price = sum(valid_prices) if valid_prices else 0
    return total_price, all_prices_retrieved


async def get_price_limited(api, ticker, semaphore, delay):
    async with semaphore:
        price = await api.get_price_from_request(ticker)
        await asyncio.sleep(delay)
        return price


def print_result(result, tickers_num, request_time, all_prices_retrieved):
    if result is not None:
        print(f"💲 Сумма цен всех тикеров: {result:.2f}")
        if not all_prices_retrieved:
            print("⚠️ Внимание: некоторые тикеры не удалось обработать.")
        else:
            print(f"🧪 Суммировали цены {tickers_num} случайных тикеров.")
        print(f"🕒 Время выполнения: {request_time:.2f} секунд.")
    else:
        print("❌ Произошла ошибка при вычислении суммы цен тикеров.")


async def main():
    async with OkxAPI() as okx_api:
        print(
            "📡 Загружаем данные биржи OKX для формирования списка тикеров для теста."
        )
        await okx_api.request_spot_data()
        tickers_list = await okx_api.get_tickers_list()

        tickers_quantity = len(tickers_list)
        tickers_num = min(5, tickers_quantity)  # для примера берем 5 тикеров
        tickers_random_list = generate_random_tickers_list(tickers_list, tickers_num)

        okx_api.reset_api_data()
        one_request_time, (result_one, all_prices_retrieved_one) = (
            await measure_time_async(
                one_request_algorithm, okx_api, tickers_random_list
            )
        )

        okx_api.reset_api_data()
        requests_frequency = 4
        many_requests_time, (result_many, all_prices_retrieved_many) = (
            await measure_time_async(
                many_requests_algorithm,
                okx_api,
                tickers_random_list,
                requests_frequency,
            )
        )

        print("\n🔎 Результаты one_request_algorithm:")
        print_result(
            result_one, tickers_num, one_request_time, all_prices_retrieved_one
        )

        print("\n🔎 Результаты many_requests_algorithm:")
        print_result(
            result_many, tickers_num, many_requests_time, all_prices_retrieved_many
        )


if __name__ == "__main__":
    asyncio.run(main())
