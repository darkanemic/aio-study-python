import asyncio
from aiohttp import ClientSession
from logger import logger
from web3 import AsyncWeb3, AsyncHTTPProvider
from web3.exceptions import TransactionNotFound
from decorators import retry, w3_error_handler
from utils import is_erc20_address_valid, is_private_key_valid

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


class W3Client:
    def __init__(self, base_url, explorer_url, proxy, client_name="Default", eip_1559=True):
        self.base_url = base_url
        self.explorer_url = explorer_url
        self.proxy = proxy
        self.client_name = client_name
        self._session = None
        self.eip_1559 = eip_1559

        self.address = None
        self._private_key = None
        self.w3 = None


    @w3_error_handler
    @retry(max_retries=3, retry_delay=2)
    async def connect(self):
        self._session = ClientSession()

        request_kwargs = {'proxy': f'http://{self.proxy}'} if self.proxy else {}
        self.w3 = AsyncWeb3(
            AsyncHTTPProvider(self.base_url, request_kwargs=request_kwargs)
        )
        if await self.is_connect():
            logger.success(f"✅ Клиент {self.client_name} успешно подключился к RPC.")
            return self
        else:
            logger.error(f"⚠️ Клиент {self.client_name}. Ошибка соединения. Закрываем сессию.")
            await self._session.close()
            raise W3NetworkConnectionError


    async def __aenter__(self):
        """
        Сессия будет автоматически открываться и закрываться в рамках асинхронного контекстного менеджера.
        """
        return await self.connect()


    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Закрытие сессии Web3 клиента.
        """
        if self._session:
            await self._session.close()
        self.w3 = None
        self._session = None


    @w3_error_handler
    @retry(max_retries=3, retry_delay=2)
    async def is_connect(self):
        return await self.w3.is_connected()


    async def close_session(self):
        """Принудительно закрыть сессию Web3."""
        if self.w3 and self.w3.provider:
            await self.w3.provider.session.close()
            logger.info("Web3 session closed.")


    @w3_error_handler
    @retry(max_retries=3, retry_delay=2)
    async def is_connect(self):
        if await self.w3.is_connected():
            return True
        else:
            return False

    @w3_error_handler
    def set_address(self, address):
        if self._private_key is None:
            if is_erc20_address_valid(self.w3, address):
                self.address = self.w3.to_checksum_address(address)
                return True
            else:
                raise ERC20AddressIncorrect
        else:
            raise ERC20AddressAlreadySet

    @w3_error_handler
    def set_private_key(self, private_key):
        if is_private_key_valid(private_key):
            self._private_key = private_key
            return True
        else:
            raise PrivateKeyIncorrect


    @w3_error_handler
    @retry(max_retries=3, retry_delay=2)
    async def get_balance(self):
        return await self.w3.eth.get_balance(self.address)


    @w3_error_handler
    async def prepare_tx(self, recipient: str,  value: int | float = 0):
        try:
            transaction = {
                'chainId': await self.w3.eth.chain_id,
                'nonce': await self.w3.eth.get_transaction_count(self.address),
                'from': self.address,
                'to': self.w3.to_checksum_address(recipient),
                'value': self.w3.to_wei(value, 'ether'),
                'gasPrice': int((await self.w3.eth.gas_price) * 1.25)
            }

            if self.eip_1559:
                del transaction['gasPrice']

                base_fee = await self.w3.eth.gas_price
                max_priority_fee_per_gas = await self.w3.eth.max_priority_fee

                if max_priority_fee_per_gas == 0:
                    #logger.info("️ℹ️Приоритетная комиссия равна 0, используем базовую комиссию.")
                    max_priority_fee_per_gas = base_fee

                try:
                    max_fee_per_gas = int(base_fee * 1.25 + max_priority_fee_per_gas)
                except Exception as e:
                    raise W3PriorityFeeCalculationError(f"Ошибка при расчете приоритетной комиссии: {e}")

                transaction['maxPriorityFeePerGas'] = max_priority_fee_per_gas
                transaction['maxFeePerGas'] = max_fee_per_gas
                transaction['type'] = '0x2'

            logger.success("✅ Транзакция успешно подготовлена.")
            return transaction

        except KeyError as e:
            raise W3TransactionPreparationError(f"⚠️Ошибка в данных при подготовке транзакции: {e}") from e
        except Exception as e:
            raise W3TransactionPreparationError(f"⚠️Неизвестная ошибка при подготовке транзакции: {e}") from e


    @w3_error_handler
    @retry(max_retries=3, retry_delay=2)
    async def sign_and_send_tx(self, transaction, without_gas=False):
        try:
            if not without_gas:
                try:
                    transaction['gas'] = int((await self.w3.eth.estimate_gas(transaction)) * 1.5)
                except Exception as e:
                    raise W3TransactionSignError(f"Ошибка при оценке газа: {e}")

            try:
                signed_raw_tx = self.w3.eth.account.sign_transaction(transaction, self._private_key).rawTransaction
            except Exception as e:
                raise W3TransactionSignError(f"Ошибка при подписании транзакции: {e}")

            try:
                tx_hash_bytes = await self.w3.eth.send_raw_transaction(signed_raw_tx)
                logger.success(
                    f"✅ Транзакция транслирована в блокчейн. Ждём подтверждения: {self.explorer_url}/tx/{tx_hash_bytes.hex()}")
            except Exception as e:
                raise W3TransactionSendError(f"Ошибка при отправке транзакции : {e}")

            return self.w3.to_hex(tx_hash_bytes)

        except Exception as e:
            raise W3TransactionSendError(f"Неизвестная ошибка при отправке транзакции: {e}") from e


    @w3_error_handler
    @retry(max_retries=3, retry_delay=2)
    async def wait_tx(self, tx_hash):
        try:
            total_time = 0
            timeout = 120
            poll_latency = 10

            while True:
                try:
                    receipts = await self.w3.eth.get_transaction_receipt(tx_hash)
                    status = receipts.get("status")
                    if status == 1:
                        logger.success(f"✅ Транзакция успешно завершена: {self.explorer_url}/tx/{tx_hash}")
                        return True
                    elif status is None:
                        await asyncio.sleep(poll_latency)
                    else:
                        logger.error(f"❌ Транзакция не удалась: {self.explorer_url}/tx/{tx_hash}")
                        return False
                except TransactionNotFound:
                    if total_time > timeout:
                        raise W3TransactionTimeoutError(f"Транзакция не завершена за {timeout} секунд.")
                    total_time += poll_latency
                    await asyncio.sleep(poll_latency)

        except Exception as e:
            raise W3TransactionReceiptError(f"Ошибка при получении данных о транзакции: {e}") from e