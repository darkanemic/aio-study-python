import asyncio
from web3 import AsyncWeb3
from web3.providers.async_rpc import AsyncHTTPProvider
from datetime import datetime


async def check_connection(w3_async_client):
    return await w3_async_client.is_connected()


def convert_timestamp_to_human(timestamp):
    human_readable_date = datetime.utcfromtimestamp(timestamp).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    return human_readable_date


def convert_hash_to_hex(hash_bytes):
    return "0x" + hash_bytes.hex()


async def input_valid_block_number(w3_async):
    while True:
        try:
            latest_block_number = await w3_async.eth.block_number
            block_number = int(input("📣 Введите номер блока сети Ethereum: "))
            if 0 < block_number < latest_block_number:
                return block_number
            else:
                raise ValueError
        except ValueError:
            print(
                "⚠️ Введите корректный номер блока сети Ethereum. "
                f"Целое положительное число, меньше чем номер последнего блока {latest_block_number}."
            )


async def main():

    w3_async = AsyncWeb3(AsyncHTTPProvider("https://eth.llamarpc.com"))

    if await check_connection(w3_async):
        block_number = await input_valid_block_number(w3_async)
        block_info = await w3_async.eth.get_block(block_number)
        timestamp = convert_timestamp_to_human(block_info["timestamp"])
        hash_hex = convert_hash_to_hex(block_info["hash"])
        transactions_number = len(block_info["transactions"])
        print(f"ℹ️ Информация о блоке: {block_number}")
        print(f"        Хеш блока: {hash_hex}")
        print(f"        Время создания блока: {timestamp}")
        print(f"        Количество транзакций в блоке: {transactions_number}")
    else:
        print("❌ Не удалось подключиться к провайдеру. Проверьте соединение и RPC. ")


if __name__ == "__main__":
    asyncio.run(main())
