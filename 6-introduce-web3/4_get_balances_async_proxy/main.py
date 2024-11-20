import asyncio
from web3 import AsyncWeb3
from web3.providers.async_rpc import AsyncHTTPProvider


async def check_connection(w3_async_client):
    return await w3_async_client.is_connected()


async def get_proxy():
    proxy = input(
        "📣 Введите адрес прокси в формате username:password@proxyserver:port :"
    )
    return proxy


async def get_address(w3_async_client):
    while True:
        address = input("📣 Введите адрес ERC20 адрес для проверки баланса :")
        is_address_correct = await is_valid_erc20_address(w3_async_client, address)
        if is_address_correct:
            return address
        else:
            print("⚠️ ERC20 адрес должен быть корректным.")


async def is_valid_erc20_address(w3_async_client, address):
    if w3_async_client.is_address(address):
        return True
    return False


async def get_balance(w3_async_client, address):
    checksum_address = w3_async_client.to_checksum_address(address)
    balance = await w3_async_client.eth.get_balance(checksum_address)
    eth_balance = w3_async_client.from_wei(balance, "ether")
    return [(checksum_address, eth_balance)]


def print_balances(balances):
    for address, balance in balances:
        print(f"💲 Баланс адреса {address}: {balance:.4f} 🇪🇹🇭")


async def main():

    proxy = await get_proxy()
    rpc_url = "https://eth.llamarpc.com"
    request_kwargs = {"proxy": f"http://{proxy}"}
    w3_async = AsyncWeb3(AsyncHTTPProvider(rpc_url, request_kwargs=request_kwargs))
    if not await check_connection(w3_async):
        print(
            "❌ Не удалось подключиться. Проверьте соединение, RPC и работоспособность вашего прокси."
        )
        return

    address = await get_address(w3_async)

    balances = await get_balance(w3_async, address)
    print_balances(balances)


if __name__ == "__main__":
    asyncio.run(main())
