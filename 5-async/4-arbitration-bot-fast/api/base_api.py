from abc import ABC, abstractmethod
from core.exceptions import LocalStorageError, DiskFullError, StoragePermissionError
from core.utils import dump_json_to_file
from core.logger import logger

class ExchangeAPI(ABC):
    def __init__(self):
        self._base_url = None
        self.spot_data = None
        self.tickers_list = None
        self.tickers_dict = None
        self.session = None

    @abstractmethod
    async def make_api_request(self, endpoint, params):
        pass

    @abstractmethod
    async def request_spot_data(self):
        pass

    @abstractmethod
    async def request_ticker_data(self, ticker):
        pass

    @abstractmethod
    async def get_tickers_list(self):
        pass

    async def save_spot_data(self, filename):
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

        return False

    @abstractmethod
    def generate_tickers_dict(self):
        pass

    @abstractmethod
    def get_price_from_dict(self, ticker):
        pass

    @abstractmethod
    async def get_price_from_request(self, ticker):
        pass

    def reset_api_data(self):
        self.spot_data = None
        self.tickers_list = None
        self.tickers_dict = None