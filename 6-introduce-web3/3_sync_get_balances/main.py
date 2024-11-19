import asyncio
from web3 import AsyncWeb3
from web3.providers.async_rpc import AsyncHTTPProvider


async def check_connection(w3_async_client):
    return await w3_async_client.is_connected()


def is_valid_erc20_address(w3_async_client, address):
    if w3_async_client.is_address(address):
        return True
    return False


async def get_balance(w3_async_client, address):
    checksum_address = w3_async_client.to_checksum_address(address)
    balance = await w3_async_client.eth.get_balance(checksum_address)
    eth_balance = w3_async_client.from_wei(balance, "ether")
    return checksum_address, eth_balance


def print_balances(balances):
    for address, balance in balances:
        print(f"💲 Баланс адреса {address}: {balance:.4f} 🇪🇹🇭")


async def main():

    address_list = (
        0x21F25E0507F363B0311F880277A23F9BB0E677A8,
        0xA9D1E08C7793AF67E9D92FE308D5697FB81D3E43,
        0x787BAA623798F149CD6B65CCF3B8E3F49F17503B,
    )

    w3_async = AsyncWeb3(AsyncHTTPProvider("https://eth.llamarpc.com"))

    if await check_connection(w3_async):
        tasks = []
        for item in address_list:
            tasks.append(asyncio.create_task(get_balance(w3_async, item)))
        balances = await asyncio.gather(*tasks)
        print_balances(balances)
    else:
        print("❌ Не удалось подключиться к провайдеру. Проверьте соединение и RPC.")


if __name__ == "__main__":
    asyncio.run(main())
