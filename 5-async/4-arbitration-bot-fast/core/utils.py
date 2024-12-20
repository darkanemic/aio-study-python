import json
import aiofiles
from core.exceptions import LocalStorageError, DiskFullError, StoragePermissionError
from core.logger import logger


async def dump_json_to_file(json_data, filename):
    try:
        async with aiofiles.open(filename, "w", encoding="utf-8") as file:
            await file.write(json.dumps(json_data, ensure_ascii=False, indent=4))
            return True
    except PermissionError as error:
        raise StoragePermissionError(
            f"Нет прав для записи в файл {filename}"
        ) from error
    except OSError as error:
        if error.errno == 28:
            raise DiskFullError(
                f"Недостаточно места на диске для сохранения {filename}"
            )
        raise LocalStorageError(
            f"Ошибка при записи файла {filename}: {error}"
        ) from error
    except Exception as error:
        raise LocalStorageError(
            f"Неизвестная ошибка при сохранении файла {filename}"
        ) from error


async def load_json_from_file(filename):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)
    except PermissionError as error:
        raise StoragePermissionError(
            f"Нет прав для чтения из файл {filename}"
        ) from error
    except OSError as error:
        if error.errno == 28:
            raise DiskFullError(f"Недостаточно места на диске для чтения {filename}")
        raise LocalStorageError(
            f"Ошибка при чтении файла {filename}: {error}"
        ) from error
    except Exception as error:
        raise LocalStorageError(
            f"Неизвестная ошибка при чтении файла {filename}"
        ) from error


def handle_http_error(status_code):
    errors = {
        400: "Ошибка 400: Неверный запрос. Проверьте параметры.",
        401: "Ошибка 401: Неавторизованный доступ. Проверьте учетные данные.",
        404: "Ошибка 404: Ресурс не найден. Проверьте URL.",
        429: "Ошибка 429: Превышено количество запросов.",
        500: "Ошибка 500: Внутренняя ошибка сервера.",
        502: "Ошибка 502: Неверный ответ шлюза.",
        503: "Ошибка 503: Сервис временно недоступен.",
    }
    error_message = errors.get(status_code, f"HTTP ошибка с кодом {status_code}.")
    logger.error(error_message)
