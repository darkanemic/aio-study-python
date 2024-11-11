from abc import ABC, abstractmethod
import json
import asyncio
import aiohttp
import aiofiles
import sys
from loguru import logger


# Настроим loguru. В файл будем писать подробно. В консоль только время, уровень и сообщение.
# Удаляем все существующие обработчики loguru
logger.remove()

# В файл будем логироватьи детально
logger.add(
    "okx_log.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} - {message}",
    rotation="1 MB",
)

# В консоль же будем выводить менее подробно
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>",
    colorize=True,
)


# Базовое исключение для всех ошибок, связанных с биржей
class ExchangeError(Exception):
    pass


# Ошибки API
class APIError(ExchangeError):
    pass


class AuthenticationError(APIError):
    pass


class RateLimitError(APIError):
    pass


class InvalidRequestError(APIError):
    pass


# Ошибки обработки данных
class DataProcessingError(ExchangeError):
    pass


# Ошибки, связанные с сетью и HTTP
class WebError(Exception):
    pass


class NetworkError(WebError):
    pass


class WebConnectionError(NetworkError):
    pass


class WebTimeoutError(NetworkError):
    pass


class HTTPError(WebError):
    pass


# Ошибки локального хранения данных
class LocalStorageError(Exception):
    pass


class DiskFullError(LocalStorageError):
    pass


class StoragePermissionError(LocalStorageError):
    pass


class ExchangeAPI(ABC):
    def __init__(self):
        self._base_url = None
        self.spot_data = None
        self.tickers_list = None
        self.tickers_dict = None
        self.session = None

    @abstractmethod
    async def make_api_request(self, endpoint, params):
        """Отправка запроса к API биржи"""
        pass

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

    async def save_spot_data(self, filename):
        """Сохраняет данные SPOT на диск и обрабатывает ошибки с логированием"""
        if self.spot_data is None:
            await self.request_spot_data()

        try:
            result = await dump_json_to_file(self.spot_data, filename)
            return result
        except StoragePermissionError as e:
            logger.error(f"Ошибка прав доступа при сохранении файла: {e}")
        except DiskFullError as e:
            logger.error(f"Недостаточно места на диске: {e}")
        except LocalStorageError as e:
            logger.error(f"Ошибка локального хранения данных: {e}")
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при сохранении данных: {e}")

        return False  # Возвращаем False, если произошла ошибка

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
            logger.error(f"❌ Ошибка соединения: {error}")
        except aiohttp.ClientPayloadError as error:
            logger.error(f"❌ Ошибка обработки данных: {error}")
        except aiohttp.ClientError as error:
            logger.error(f"❌ Произошла ошибка при попытке запроса: {error}")
        return None

    async def request_spot_data(self):
        endpoint = "/market/tickers"
        params = {"instType": "SPOT"}
        exchange_response = await self.make_api_request(endpoint, params)
        if exchange_response:
            logger.info("✅ Успешно получили данные SPOT рынка биржи OKX.")
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
            raise ValueError("Spot data is not loaded.")
        return [item["instId"] for item in self.spot_data["data"]]

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


def handle_http_error(status_code):
    errors = {
        400: "❌ Ошибка 400: Неверный запрос. Проверьте корректность параметров запроса.",
        401: "❌ Ошибка 401: Неавторизованный доступ. Проверьте токен или учетные данные.",
        404: "❌ Ошибка 404: Ресурс не найден. Проверьте правильность URL.",
        429: "❌ Ошибка 429: Превышено количество запросов. Попробуйте уменьшить частоту запросов.",
        500: "❌ Ошибка 500: Внутренняя ошибка сервера. Попробуйте снова позже.",
        502: "❌ Ошибка 502: Неверный ответ шлюза. Возможно, сервер перегружен.",
        503: "❌ Ошибка 503: Сервис временно недоступен. Сервер перегружен или на обслуживании.",
    }
    error_message = errors.get(
        status_code, f"Произошлa HTTP ошибка с кодом {status_code}."
    )
    logger.error(error_message)


async def dump_json_to_file(json_data, filename):
    """Асинхронная функция для сохранения данных JSON на диск с обработкой ошибок."""
    try:
        async with aiofiles.open(filename, "w", encoding="utf-8") as file:
            await file.write(json.dumps(json_data, ensure_ascii=False, indent=4))
            return True  # Успешно записано

    except PermissionError as error:
        raise StoragePermissionError(
            f"Нет прав для записи в файл {filename}"
        ) from error

    except OSError as error:
        exception_map = {
            28: DiskFullError(f"Недостаточно места на диске для сохранения {filename}"),
        }
        raise exception_map.get(
            error.errno,
            LocalStorageError(f"Ошибка при записи файла {filename}: {error}"),
        ) from error

    except Exception as error:
        raise LocalStorageError(
            f"Неизвестная ошибка при сохранении файла {filename}"
        ) from error


async def main():
    async with OkxAPI() as okx_api:
        logger.info("📣 Подготовимся к запуску теста...")
        logger.info(
            "📡 Загружаем данные биржи OKX для формирования списка тикеров для теста."
        )
        await okx_api.request_spot_data()
        tickers_list = await okx_api.get_tickers_list()

        # Сохраним spot-data в файл как указано в дз
        if await okx_api.save_spot_data("//okx-spot-data.json"):
            logger.info(
                "✅ SPOT данные биржи OKX успешно сохранены в okx-spot-data.json."
            )
        else:
            logger.error("❌ SPOT данные биржи OKX не удалось сохранить.")


if __name__ == "__main__":
    asyncio.run(main())
