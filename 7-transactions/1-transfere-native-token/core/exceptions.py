class W3UnknownError(Exception):
    """Неизвестная ошибка при работе с Web3."""
    def __init__(self, message, cause=None):
        self.message = message
        self.cause = cause
        super().__init__(message)


class ERC20AddressIncorrect(Exception):
    """Некорректный ERC20 адрес."""
    pass

class W3NetworkConnectionError(Exception):
    """Ошибка соединения с сетью Web3."""
    pass

class W3ServerTimeoutError(Exception):
    """Ошибка: превышено время ожидания ответа от сервера Web3."""
    pass

class ERC20AddressAlreadySet(Exception):
    """Ошибка: адрес ERC20 уже задан."""
    pass

class PrivateKeyIncorrect(Exception):
    """Ошибка: некорректный приватный ключ."""
    pass

class UnknownMeasurementUnit(Exception):
    """Ошибка: неизвестная единица измерения для конвертации."""
    pass

class W3PriorityFeeError(Exception):
    """Ошибка при вычислении приоритетной комиссии."""
    pass

class W3EmptyFeeHistoryError(Exception):
    """Ошибка: История комиссий пуста или данные отсутствуют."""
    pass

class W3TransactionPreparationError(Exception):
    """Ошибка при подготовке транзакции."""
    pass

class W3PriorityFeeCalculationError(Exception):
    """Ошибка при расчете приоритетной комиссии."""
    pass

class W3TransactionSignError(Exception):
    """Ошибка при подписании транзакции."""
    pass

class W3TransactionSendError(Exception):
    """Ошибка при отправке транзакции."""
    pass

class W3TransactionReceiptError(Exception):
    """Ошибка при получении данных о транзакции."""
    pass

class W3TransactionTimeoutError(Exception):
    """Ошибка: превышено время ожидания подтверждения транзакции."""
    pass