import requests
from abc import ABC, abstractmethod
import json
import asyncio
import aiohttp


def handle_http_error(http_error):
    status_code = http_error.response.status_code if http_error.response else None
    errors = {
        400: "❌ Ошибка 400: Неверный запрос. Проверьте корректность параметров запроса.",
        401: "❌ Ошибка 401: Неавторизованный доступ. Проверьте токен или учетные данные.",
        404: "❌ Ошибка 404: Ресурс не найден. Проверьте правильность URL.",
        429: "❌ Ошибка 429: Превышено количество запросов. Попробуйте снова позже или используйте прокси.",
        500: "❌ Ошибка 500: Внутренняя ошибка сервера. Попробуйте снова позже.",
        502: "❌ Ошибка 502: Неверный ответ шлюза. Возможно, сервер перегружен.",
        503: "❌ Ошибка 503: Сервис временно недоступен. Сервер перегружен или на обслуживании.",
    }
    print(errors.get(status_code, f"Произошла HTTP ошибка с кодом {status_code}."))


def dump_json_to_file(json_data, filename, message):
    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(json_data, file, ensure_ascii=False, indent=4)
            if message:
                print(message)
    except OSError as error:
        print(
            f"❌ Ошибка {error} при записи файла {filename}. Возможно не хватает прав доступа. Программа завершена."
        )
        exit()


class ExchangeAPI(ABC):
    @abstractmethod
    def fetch_spot_data(self):
        pass


class OkxAPI(ExchangeAPI):
    OKX_BASE_URL = "https://www.okx.com/api/v5"

    # переделать в async
    def fetch_spot_data(self):
        endpoint = "/market/tickers"
        params = {"instType": "SPOT"}
        try:
            url = f"{self.OKX_BASE_URL}{endpoint}"
            exchange_response = requests.get(url, params=params)
            exchange_response.raise_for_status()
            print("✅ Успешно получили данные SPOT рынка биржи OKX.")
            return exchange_response.json()
        except requests.exceptions.HTTPError as http_error:
            handle_http_error(http_error)
        except requests.exceptions.ConnectionError as error:
            print(f"❌ Ошибка соединения: {error}")
        except requests.exceptions.Timeout as error:
            print(f"❌ Превышено время ожидания: {error}")
        except requests.exceptions.RequestException as error:
            print(f"❌ Произошла ошибка при попытке запроса: {error}")
        return None


if __name__ == "__main__":
    okx_api = OkxAPI()
    spot_data = okx_api.fetch_spot_data()
    dump_json_to_file(
        spot_data,
        "../okx-spot-data.json",
        "✅ SPOT данные биржи OKX успешно сохранены.",
    )
