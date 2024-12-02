import time
import asyncio
from logger import logger
from exceptions import (
    W3UnknownError,
    ERC20AddressIncorrect,
    W3NetworkConnectionError,
    W3ServerTimeoutError,
    ERC20AddressAlreadySet,
    PrivateKeyIncorrect,
    UnknownMeasurementUnit,
    W3PriorityFeeError,
    W3EmptyFeeHistoryError,
    W3TransactionPreparationError,
    W3PriorityFeeCalculationError,
    W3TransactionSignError,
    W3TransactionSendError,
    W3TransactionReceiptError,
    W3TransactionTimeoutError,
)

def retry(max_retries=3, retry_delay=1):
    """
    Декоратор для повторных запросов к RPC с обработкой исключений и задержкой между попытками.
    """
    def decorator(func):
        if asyncio.iscoroutinefunction(func):  # Проверяем, является ли функция асинхронной
            async def wrapper(*args, **kwargs):
                retries = 0
                while retries < max_retries:
                    try:
                        return await func(*args, **kwargs)
                    except (ConnectionError, TimeoutError) as e:
                        retries += 1
                        logger.error(f"⚠️ Ошибка соединения: {e}"
                                     f"\n⚠️ Повторная попытка через {retry_delay} секунд"
                                     f"\n⚠️ Попытка {retries} из {max_retries}")
                        if retries < max_retries:
                            await asyncio.sleep(retry_delay)
                            continue
                        raise e  # Если попытки исчерпаны, пробрасываем исключение
                    except Exception as e:
                        raise e  # Пробрасываем остальные исключения
            return wrapper
        else:
            def wrapper(*args, **kwargs):  # Для синхронных функций
                retries = 0
                while retries < max_retries:
                    try:
                        return func(*args, **kwargs)
                    except (ConnectionError, TimeoutError) as e:
                        retries += 1
                        logger.error(f"⚠️ Ошибка соединения: {e}"
                                     f"\n⚠️ Повторная попытка через {retry_delay} секунд"
                                     f"\n⚠️ Попытка {retries} из {max_retries}")
                        if retries < max_retries:
                            time.sleep(retry_delay)
                            continue
                        raise e  # Если попытки исчерпаны, пробрасываем исключение
                    except Exception as e:
                        raise e  # Пробрасываем остальные исключения
            return wrapper
    return decorator


def handle_w3_error(e):
    """
    Универсальная функция для обработки ошибок Web3.
    """
    if isinstance(e, ERC20AddressIncorrect):
        logger.error(
            "⚠️ Некорректный ERC20 адрес. Проверьте формат. "
            "📢 Адрес должен начинаться с префикса 0x и содержать 40 шестнадцатеричных символов (0-9, A-F)."
        )
        raise e
    elif isinstance(e, ERC20AddressAlreadySet):
        logger.error(
            "⚠️ Уже задан ERC20 адрес через назначение приватного ключа. Сначала сбросите приватный ключ на None."
        )
        raise e
    elif isinstance(e, PrivateKeyIncorrect):
        logger.error(
            "⚠️ Некорректный приватный ключ. Проверьте формат."
            "📢 Приватный ключ — это строка длиной 64 символа в шестнадцатеричном формате (0-9, a-f) без префикса 0x"
            "📢 или 66 символов с префиксом 0x"
        )
        raise e
    elif isinstance(e, UnknownMeasurementUnit):
        logger.error(
            "⚠️ Некорректный приватный ключ. Проверьте формат."
            "📢 Приватный ключ — это строка длиной 64 символа в шестнадцатеричном формате (0-9, a-f) без префикса 0x"
            "📢 или 66 символов с префиксом 0x"
        )
        raise e
    elif isinstance(e, W3PriorityFeeError):
        logger.error(
            "⚠️ Ошибка при вычислении приоритетной комиссии. "
            "⛔ Убедитесь, что RPC-сервер предоставляет корректные данные."
        )
        raise e
    elif isinstance(e, W3EmptyFeeHistoryError):
        logger.error(
            "⚠️ История комиссий пуста или данные некорректны. "
            "⛔ Проверьте RPC-сервер и повторите попытку."
        )
        raise e
    elif isinstance(e, W3NetworkConnectionError):
        logger.error(
            "⚠️ Ошибка соединения. Проверьте интернет, RPC-сервер и прокси. "
            "⛔️ Исправьте конфигурацию и повторите попытку."
        )
        exit(1)
    elif isinstance(e, W3ServerTimeoutError):
        logger.error(
            "⚠️ Превышение времени ожидания. Возможно, сервер перегружен. "
            "⛔ Повторите попытку позже."
        )
        exit(1)
    elif isinstance(e, W3UnknownError):
        logger.error(
            f"⚠️ Неизвестная ошибка при работе с Web3: {e}. "
            f"⛔ Устраните причину и перезапустите программу."
        )
        exit(1)
    else:
        logger.error(f"⚠️ Непредвиденная ошибка: {e}")
        exit(1)


def w3_error_handler(func):
    """
    Декоратор для обработки ошибок взаимодействия с Web3.
    """
    if asyncio.iscoroutinefunction(func):  # Проверяем, является ли функция асинхронной
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                handle_w3_error(e)
        return wrapper
    else:
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handle_w3_error(e)
        return wrapper