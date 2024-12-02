import sys
from loguru import logger
from eth_account import Account
from exceptions import ERC20AddressIncorrect, W3NetworkConnectionError, W3ServerTimeoutError, W3UnknownError
from decorators import w3_error_handler, retry


def is_private_key_valid(private_key: str) -> bool:
    try:
        Account.from_key(private_key)
        return True
    except ValueError:
        return False


def is_erc20_address_valid(w3_client, address) -> bool:
    try:
        address = w3_client.to_checksum_address(address)
        if w3_client.is_address(address):
            return True
    except ValueError:
        return False

def is_value_valid(value: str) -> bool:
    try:
        value = float(value)
        if value > 0:
            return True
    except ValueError:
        logger.warning(f"⚠️ Некорректное значение: {value}. Ожидается ввод положительного числа, с плавающей точкой. Например: 0.0001")
        return False

def wait_until_confirm(message):
    try:
        while True:
            answer = input(message)
            if answer.lower() == "y":
                return True
            elif answer.lower() == "n":
                return False
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Выполнение прервано пользователем.")
        sys.exit(130)