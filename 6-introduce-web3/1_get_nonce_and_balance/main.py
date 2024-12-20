import asyncio
from web3 import AsyncWeb3
from web3.providers.async_rpc import AsyncHTTPProvider


async def check_connection(w3_async_client):
    return await w3_async_client.is_connected()


def is_valid_erc20_address(w3_async_client, address):
    if w3_async_client.is_address(address):
        return True
    return False


async def main():

    w3_async = AsyncWeb3(AsyncHTTPProvider("https://1rpc.io/linea"))
    address = input("📣 Введите ERC20 адрес: ")
    while not is_valid_erc20_address(w3_async, address):
        address = input("⚠️ Введите корректный ERC20(0x...) адрес: ")
    if await check_connection(w3_async):
        checksum_address = w3_async.to_checksum_address(address)
        balance = await w3_async.eth.get_balance(checksum_address)
        eth_balance = w3_async.from_wei(balance, "ether")
        nonce = await w3_async.eth.get_transaction_count(checksum_address)
        print(
            f"💲 Баланс данного адреса: {eth_balance:.4f} 🇪🇹🇭\n🧮 Количество транзакций: {nonce}"
        )
    else:
        print("❌ Не удалось подключиться к провайдеру. Проверьте соединение.")


if __name__ == "__main__":
    asyncio.run(main())
