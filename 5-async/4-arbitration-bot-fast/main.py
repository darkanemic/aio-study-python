import asyncio
from api.exchanges.okx_api import OkxAPI
from core.logger import logger

async def main():
    async with OkxAPI() as okx_api:
        logger.info("Запуск теста...")
        await okx_api.request_spot_data()
        tickers_list = await okx_api.get_tickers_list()

        if await okx_api.save_spot_data("okx-spot-data.json"):
            logger.info("SPOT данные биржи OKX успешно сохранены в okx-spot-data.json.")
        else:
            logger.error("Не удалось сохранить SPOT данные биржи OKX.")

if __name__ == "__main__":
    asyncio.run(main())