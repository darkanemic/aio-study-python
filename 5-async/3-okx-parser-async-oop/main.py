from abc import ABC, abstractmethod
import json
import random
import time
import asyncio
import aiohttp
import aiofiles


class ExchangeAPI(ABC):

    def __init__(self):
        self.base_url = None
        self.spot_data = None
        self.tickers_list = None
        self.tickers_dict = None

    @abstractmethod
    async def request_spot_data(self):
        pass

    @abstractmethod
    async def request_ticker_data(self, ticker):
        pass

    @abstractmethod
    async def get_tickers_list(self):
        pass

    @abstractmethod
    async def save_spot_data(self, filename):
        pass

    @abstractmethod
    async def generate_tickers_dict(self):
        pass

    @abstractmethod
    async def get_price_from_dict(self, ticker):
        pass

    @abstractmethod
    async def get_price_from_request(self, ticker):
        pass

    @abstractmethod
    async def reset_api_data(self):
        pass


class OkxAPI(ExchangeAPI):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.okx.com/api/v5"

    async def request_spot_data(self):
        endpoint = "/market/tickers"
        params = {"instType": "SPOT"}
        try:
            url = f"{self.base_url}{endpoint}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    response.raise_for_status()
                    exchange_response = await response.json()
            print("✅ Успешно получили данные SPOT рынка биржи OKX.")
            self.spot_data = exchange_response
            return True
        except aiohttp.ClientResponseError as http_error:
            handle_http_error(http_error.status)
        except aiohttp.ClientConnectionError as error:
            print(f"❌ Ошибка соединения: {error}")
        except aiohttp.ClientPayloadError as error:
            print(f"❌ Ошибка обработки данных: {error}")
        except aiohttp.ClientError as error:
            print(f"❌ Произошла ошибка при попытке запроса: {error}")
        return False

    async def request_ticker_data(self, ticker):
        endpoint = "/market/ticker"
        params = {"instId": ticker}
        try:
            url = f"{self.base_url}{endpoint}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    response.raise_for_status()
                    exchange_response = await response.json()
            return exchange_response
        except aiohttp.ClientResponseError as http_error:
            handle_http_error(http_error.status)
        except aiohttp.ClientConnectionError as error:
            print(f"❌ Ошибка соединения: {error}")
        except aiohttp.ClientPayloadError as error:
            print(f"❌ Ошибка обработки данных: {error}")
        except aiohttp.ClientError as error:
            print(f"❌ Произошла ошибка при попытке запроса: {error}")
        return None

    async def get_tickers_list(self):
        if self.spot_data is None:
            self.spot_data = await self.request_spot_data()
        tickers_list = [item["instId"] for item in self.spot_data["data"]]
        return tickers_list

    async def save_spot_data(self, filename):
        if self.spot_data is None:
            self.spot_data = await self.request_spot_data()
        dump_data = await dump_json_to_file(self.spot_data, filename)
        if dump_data == "Success":
            print(f"💾 SPOT данные биржи OKX успешно сохранены в файл {filename}.")
        else:
            print("❌ SPOT данные биржи OKX не удалось сохранить.")
            handle_file_dump_error(dump_data)
            print(f"⛔ Устраните проблему и перезапустите программу.")
            exit()

    async def generate_tickers_dict(self):
        if self.spot_data is None:
            self.spot_data = await self.request_spot_data()
        if self.spot_data is None:
            print("❌ Не удалось получить данные тикеров.")
            return None

        self.tickers_dict = {item["instId"]: item for item in self.spot_data["data"]}
        return True

    async def get_price_from_dict(self, ticker):
        if self.tickers_dict is None:
            tickers_dict = await self.generate_tickers_dict()
        else:
            tickers_dict = self.tickers_dict
        if ticker in tickers_dict:
            return float(tickers_dict[ticker]["last"])
        else:
            print(f"❌ Тикер {ticker} не найден.")

    async def get_price_from_request(self, ticker):
        request_response = await self.request_ticker_data(ticker)
        if (
            request_response is not None
            and "data" in request_response
            and len(request_response["data"]) > 0
        ):
            last_price = request_response["data"][0].get("last")
            if last_price is not None:
                try:
                    price = float(last_price)
                    return price
                except ValueError:
                    print(f"❌ Неверный формат цены для тикера {ticker}: {last_price}")
                    return None
            else:
                print(
                    f"❌ Ключ 'last' отсутствует или имеет значение None для тикера {ticker}"
                )
                return None
        else:
            print(f"❌ Некорректный ответ для тикера {ticker}. Данные отсутствуют.")
            return None

    async def reset_api_data(self):
        self.spot_data = None
        self.tickers_list = None
        self.tickers_dict = None


def ask_number_in_range(prompt, min_value, max_value):
    while True:
        user_input = input(prompt)
        if user_input.isdigit():
            number = int(user_input)
            if min_value <= number <= max_value:
                return number
            else:
                print(
                    f"❌ Введенное значение должно быть в диапазоне от {min_value} до {max_value}. Попробуйте ещё раз."
                )
        else:
            print("❌ Введенное значение должно быть числом. Попробуйте ещё раз.")


def handle_http_error(status_code):
    errors = {
        400: "❌ Ошибка 400: Неверный запрос. Проверьте корректность параметров запроса.",
        401: "❌ Ошибка 401: Неавторизованный доступ. Проверьте токен или учетные данные.",
        404: "❌ Ошибка 404: Ресурс не найден. Проверьте правильность URL.",
        429: "❌ Ошибка 429: Превышено количество запросов. Попробуйте снова позже или используйте прокси.",
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


async def get_price_limited(api, ticker, semaphore):
    # Ограничиваем доступ к ресурсу с помощью семафора
    async with semaphore:
        return await api.get_price_from_request(ticker)


async def dump_json_to_file(json_data, filename):
    try:
        async with aiofiles.open(filename, "w", encoding="utf-8") as file:
            await file.write(json.dumps(json_data, ensure_ascii=False, indent=4))
            dump_success = "Success"  # Если успешно записано, устанавливаем статус
    except (TypeError, OverflowError, ValueError, OSError, UnicodeEncodeError) as error:
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


def print_result(result, tickers_num, request_time):
    if result is not None:
        print(f"💲 Сумма цен всех тикеров: {result:.2f}")
        print(f"🧪 Суммировали цены {tickers_num} случайных тикеров.")
        print(f"🕒 Время выполнения: {request_time:.2f} секунд.")
    else:
        print("❌ Произошла ошибка при вычислении суммы цен тикеров.")


async def one_request_algorithm(api, tickers_list):
    print(f"\n🚀 Запускаем one_request_algorithm")
    await api.request_spot_data()  # Загружаем spot-data
    await api.generate_tickers_dict()  # Генерируем из spot-data словарь tickers-dict
    prices = await asyncio.gather(
        *(api.get_price_from_dict(ticker) for ticker in tickers_list)
    )
    total_price = sum(prices)
    if total_price is None:
        return None
    else:
        print(f"🟢 Алгоритм one_request_algorithm успешно отработал!")
        return total_price


async def many_requests_algorithm(api, tickers_list):
    semaphore = asyncio.Semaphore(5)  # Ограничиваем до X запросов в секунду
    print(f"\n🚀 Запускаем many_request_algorithm")
    tasks = [get_price_limited(api, ticker, semaphore) for ticker in tickers_list]
    prices = await asyncio.gather(*tasks)
    total_price = sum(prices)
    if total_price is None:
        return None
    else:
        print(f"🟢 Алгоритм many_request_algorithm успешно отработал!")
        return total_price


async def main():
    okx_api = OkxAPI()

    # подготовимся к тесту
    print("📣 Подготовимся к запуску теста...")
    print("📡 Загружаем данные биржи OKX для формирования списка тикеров для теста.")
    await okx_api.request_spot_data()
    tickers_list = await okx_api.get_tickers_list()

    # Сохраним spot-data в файл как указано в дз
    await okx_api.save_spot_data("okx-spot-data.json")

    tickers_quantity = len(tickers_list)
    print(f"📣 Всего на бирже найдено {tickers_quantity} тикеров. ")

    # Спросим количество тикеров а которых будем тестировать
    tickers_num = ask_number_in_range(
        f"\nВведите количество тикеров на котором будем тестировать (от 1 до {tickers_quantity}): ",
        1,
        tickers_quantity,
    )

    # Сгенерируем рандомный список тикеров для теста
    tickers_random_list = generate_random_tickers_list(tickers_list, tickers_num)
    print(f"\n📣 Будем тестировать на {tickers_num} тикерах.")

    # Замер времени выполнения one_request_algorithm
    await okx_api.reset_api_data()  # Сбросим состояние API
    one_request_time, result_one = await measure_time_async(
        one_request_algorithm, okx_api, tickers_random_list
    )

    # Замер времени выполнения many_requests_algorithm
    await okx_api.reset_api_data()  # Сбросим состояние API
    many_requests_time, result_many = await measure_time_async(
        many_requests_algorithm, okx_api, tickers_random_list
    )

    # Выведем результаты
    print("\n🔎 Результаты one_request_algorithm.\n")
    print_result(result_one, tickers_num, one_request_time)
    print("\n🔎 Результаты many_request_algorithm.\n")
    print_result(result_many, tickers_num, many_requests_time)


if __name__ == "__main__":
    asyncio.run(main())
