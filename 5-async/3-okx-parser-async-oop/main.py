from abc import ABC, abstractmethod
import json
import time
import random
import asyncio
import aiohttp
import aiofiles


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
            handle_http_error(http_error.status)
        except aiohttp.ClientConnectionError as error:
            print(f"❌ Ошибка соединения: {error}")
        except aiohttp.ClientPayloadError as error:
            print(f"❌ Ошибка обработки данных: {error}")
        except aiohttp.ClientError as error:
            print(f"❌ Произошла ошибка при попытке запроса: {error}")
        return None

    async def request_spot_data(self):
        endpoint = "/market/tickers"
        params = {"instType": "SPOT"}
        exchange_response = await self.make_api_request(endpoint, params)
        if exchange_response:
            print("✅ Успешно получили данные SPOT рынка биржи OKX.")
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
            print(
                f"❌ Ошибка при получении данных для тикера {ticker}: {exchange_response}"
            )
            return None

    async def get_tickers_list(self):
        if self.spot_data is None:
            raise ValueError("Spot data is not loaded.")
        return [item["instId"] for item in self.spot_data["data"]]

    async def save_spot_data(self, filename):
        if self.spot_data is None:
            await self.request_spot_data()
        dump_data = await dump_json_to_file(self.spot_data, filename)
        if dump_data:
            return True
        else:
            handle_file_dump_error(dump_data)
            return False

    def generate_tickers_dict(self):
        if self.spot_data is None:
            self.request_spot_data()
        self.tickers_dict = {item["instId"]: item for item in self.spot_data["data"]}
        return True

    def get_price_from_dict(self, ticker):
        if self.tickers_dict is None:
            self.generate_tickers_dict()
        if ticker in self.tickers_dict:
            return float(self.tickers_dict[ticker]["last"])
        else:
            print(f"❌ Тикер {ticker} не найден.")
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
                    print(f"❌ Неверный формат цены для тикера {ticker}: {last_price}")
            else:
                print(f"❌ Цена отсутствует для тикера {ticker}")
        else:
            print(f"❌ Некорректный ответ для тикера {ticker}: {request_response}")
        return None


def ask_number_in_range(prompt, min_value, max_value):
    while True:
        user_input = input(prompt)
        try:
            number = int(user_input)
            if min_value <= number <= max_value:
                return number
            else:
                print(
                    f"❌ Введенное значение должно быть в диапазоне от {min_value} до {max_value}. Попробуйте ещё раз."
                )
        except ValueError:
            print("❌ Введенное значение должно быть числом. Попробуйте ещё раз.")


def handle_http_error(status_code):
    errors = {
        400: "❌ Ошибка 400: Неверный запрос. Проверьте корректность параметров запроса.",
        401: "❌ Ошибка 401: Неавторизованный доступ. Проверьте токен или учетные данные.",
        404: "❌ Ошибка 404: Ресурс не найден. Проверьте правильность URL.",
        429: "❌ Ошибка 429: Превышено количество запросов. Попробуйте в настройках "
        "уменьшить request_frequency(частоту запросов).",
        500: "❌ Ошибка 500: Внутренняя ошибка сервера. Попробуйте снова позже.",
        502: "❌ Ошибка 502: Неверный ответ шлюза. Возможно, сервер перегружен.",
        503: "❌ Ошибка 503: Сервис временно недоступен. Сервер перегружен или на обслуживании.",
    }
    error_message = errors.get(
        status_code, f"Произошлa HTTP ошибка с кодом {status_code}."
    )
    print(error_message)


def handle_file_dump_error(file_error):
    if isinstance(file_error, FileNotFoundError):
        print(f"❌ Директория для файла '{file_error.filename}' не существует.")
    else:
        response = getattr(file_error, "response", None)
        status_code = getattr(response, "status_code", None)

        errors = {
            TypeError: "❌ TypeError: Объект содержит несериализуемые данные или файл открыт в неверном режиме.",
            OverflowError: "❌ OverflowError: Число слишком велико для JSON.",
            ValueError: "❌ ValueError: Ошибка в структуре данных или неверный параметр.",
            OSError: "❌ OSError: Ошибка доступа к файлу. Предоставьте права доступа к файлу.",
            UnicodeEncodeError: "❌ UnicodeEncodeError: Невозможно преобразовать строку в кодировку UTF-8.",
        }

        error_message = errors.get(
            type(file_error), f"Произошла ошибка с кодом {status_code}."
        )
        print(error_message)


async def get_price_limited(api, ticker, semaphore, delay):
    async with semaphore:
        price = await api.get_price_from_request(ticker)
        await asyncio.sleep(delay)
        return price


async def dump_json_to_file(json_data, filename):
    try:
        async with aiofiles.open(filename, "w", encoding="utf-8") as file:
            await file.write(json.dumps(json_data, ensure_ascii=False, indent=4))
            dump_success = True  # Если успешно записано, устанавливаем статус
    except Exception as error:
        dump_success = error  # В случае ошибки возвращаем её для анализа
    return dump_success


def generate_random_tickers_list(all_tickers_list, number_of_tickers):
    return random.sample(all_tickers_list, number_of_tickers)


async def measure_time_async(func, *args, **kwargs):
    """Функция для замера времени выполнения асинхронной функции"""
    start_time = time.perf_counter()
    result = await func(*args, **kwargs)  # вызов исходной асинхронной функции
    end_time = time.perf_counter()
    duration = end_time - start_time
    return duration, result  # возвращаем время выполнения и результат работы функции


def print_result(result, tickers_num, request_time, all_prices_retrieved):
    if result is not None:
        print(f"💲 Сумма цен всех тикеров: {result:.2f}")
        if not all_prices_retrieved:
            print("⚠️ Внимание: некоторые тикеры не удалось обработать.")
            print(
                "⚠️ Изучите сообщения об ошибках и перезапустите программу с другими настройками."
            )
        else:
            print(f"🧪 Суммировали цены {tickers_num} случайных тикеров.")
        print(f"🕒 Время выполнения: {request_time:.2f} секунд.")

    else:
        print("❌ Произошла ошибка при вычислении суммы цен тикеров.")


async def one_request_algorithm(api, tickers_list):
    print(f"\n🚀 Запускаем one_request_algorithm")
    await api.request_spot_data()  # Загружаем spot-data
    api.generate_tickers_dict()  # Генерируем из spot-data словарь tickers_dict

    all_prices_retrieved = True
    prices = []

    for ticker in tickers_list:
        price = api.get_price_from_dict(ticker)
        if price is not None:
            prices.append(price)
        else:
            all_prices_retrieved = (
                False  # Сбрасываем флаг, если не удалось получить цену
            )

    total_price = sum(prices) if prices else 0

    return total_price, all_prices_retrieved


async def many_requests_algorithm(api, tickers_list, request_frequency):
    semaphore = asyncio.Semaphore(request_frequency)
    delay = 1 / request_frequency
    print(f"🚀 Запускаем many_requests_algorithm")

    tasks = [
        get_price_limited(api, ticker, semaphore, delay) for ticker in tickers_list
    ]

    prices = await asyncio.gather(*tasks, return_exceptions=True)
    valid_prices = []
    all_prices_retrieved = True

    for price in prices:
        if isinstance(price, Exception):
            all_prices_retrieved = False
            print(f"❌ Ошибка при получении цены: {price}")
        elif price is not None:
            valid_prices.append(price)
        else:
            all_prices_retrieved = False

    total_price = sum(valid_prices) if valid_prices else 0

    return total_price, all_prices_retrieved


async def main():
    async with OkxAPI() as okx_api:
        # подготовимся к тесту
        print("📣 Подготовимся к запуску теста...")
        print(
            "📡 Загружаем данные биржи OKX для формирования списка тикеров для теста."
        )
        await okx_api.request_spot_data()
        tickers_list = await okx_api.get_tickers_list()

        # Сохраним spot-data в файл как указано в дз
        if await okx_api.save_spot_data("okx-spot-data.json"):
            print("✅ SPOT данные биржи OKX успешно сохранены в okx-spot-data.json.")
        else:
            print("❌ SPOT данные биржи OKX не удалось сохранить.")

        tickers_quantity = len(tickers_list)
        print(f"📣 Всего на бирже найдено {tickers_quantity} тикеров. ")

        # Спросим количество тикеров на которых будем тестировать
        tickers_num = ask_number_in_range(
            f"\nВведите количество тикеров на котором будем тестировать (от 1 до {tickers_quantity}): ",
            1,
            tickers_quantity,
        )

        # Сгенерируем рандомный список тикеров для теста
        tickers_random_list = generate_random_tickers_list(tickers_list, tickers_num)
        print(f"📣 Будем тестировать на {tickers_num} тикерах.")

        # Замер времени выполнения one_request_algorithm
        okx_api.reset_api_data()  # Сбросим состояние API
        one_request_time, (result_one, all_prices_retrieved_one) = (
            await measure_time_async(
                one_request_algorithm, okx_api, tickers_random_list
            )
        )

        # Замер времени выполнения many_requests_algorithm
        okx_api.reset_api_data()  # Сбросим состояние API
        # Количество запросов в секунду (уменьшите, если получаете ошибку too many requests)
        # При большом количестве запрашиваемых данных лучше не превышать частоту 4 запроса в секунду.
        requests_frequency = 4
        many_requests_time, (result_many, all_prices_retrieved_many) = (
            await measure_time_async(
                many_requests_algorithm,
                okx_api,
                tickers_random_list,
                requests_frequency,
            )
        )

        # Вывод результатов через print_result
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
