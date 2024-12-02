import sys
import os
import getpass
from web3 import Web3


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'core')))
import asyncio
from core import W3Client, logger, is_value_valid, wait_until_confirm
from core import (
    ERC20AddressIncorrect,
    ERC20AddressAlreadySet,
    PrivateKeyIncorrect,
    )


def set_client_address(w3_client, message):
    while True:
        try:
            client_address = input(message)
            try:
                w3_client.set_address(client_address)
            except ERC20AddressIncorrect:
                continue
            except ERC20AddressAlreadySet:
                return False
            return True
        except KeyboardInterrupt:
            logger.warning("\n⚠️ Выполнение прервано пользователем.")
            sys.exit(130)


def set_client_private_key(w3_client, message):
    while True:
        try:
            try:
                # Попытка использовать getpass. Попробуем скрыть ввод приватного ключа в целях безопасности
                private_key = getpass.getpass(message)
            except getpass.GetPassWarning:
                # Если запуск из консоли не поддерживающей getpass, то будем использовать обычный input
                logger.info("⚠️ Приватный ключ будет отображаться при вводе. Так как консоль не поддерживает безопасный ввод.")
                private_key = input(message)

            w3_client.set_private_key(private_key)
        except PrivateKeyIncorrect:
            continue
        except KeyboardInterrupt:
            logger.warning("\n⚠️ Выполнение прервано пользователем.")
            sys.exit(130)
        return True


def get_amount_to_send(message):
    while True:
        try:
            amount = input(message)
            if is_value_valid(amount):
                return amount
            else:
                continue
        except KeyboardInterrupt:
            logger.warning("\n⚠️ Выполнение прервано пользователем.")
            sys.exit(130)


async def update_balance(w3_client):
    balance_wei = await w3_client.get_balance()
    balance_eth = w3_client.w3.from_wei(balance_wei, 'ether')
    return balance_wei, balance_eth

async def quantity_check(w3_client, transaction):
    """
    Эта функция поможет нам понять - не превышает ли (сумму перевода + gas), баланс отправителя.
    """
    try:
        check = int((await w3_client.w3.eth.estimate_gas(transaction)) * 1.5)
    except ValueError as e:
        if "insufficient funds" in str(e):
            logger.error("❌ Недостаточно средств для выполнения транзакции. Пополните баланс или уменьшите сумму перевода.")
            return False
        else:
            logger.error(f"❌ Ошибка оценки: {str(e)}")
            return False
    return check


async def main():
    base_url = "https://arbitrum.llamarpc.com"
    explorer_url = "https://arbiscan.io"
    proxy = None
    eip_1559 = True


    logger.warning("⚠️ Для запуска желательно использовать терминал, вместо консоли IDE, в этом случае ввод приватного ключа будет скрыт.")
    async with W3Client(base_url, explorer_url, proxy, "Sender", eip_1559) as sender, \
               W3Client(base_url, explorer_url, proxy, "Recipient", eip_1559) as recipient:

        set_client_address(sender, "📢 Введите адрес отправителя :")
        set_client_private_key(sender, "📢 Введите приватный ключ отправителя (⚠️ ввод будет скрыт, после ввода нажмите Enter) :")
        set_client_address(recipient, "📢 Введите адрес получателя :")


        while True:
            sender_balance_wei, sender_balance_eth = await update_balance(sender)
            recipient_balance_wei, recipient_balance_eth = await update_balance(recipient)

            logger.info(f"💰 Баланс отправителя: {sender_balance_eth:.5f} eth")
            logger.info(f"💰 Баланс получателя: {recipient_balance_eth:.5f} eth")

            amount_eth = get_amount_to_send("📢 Введите количество Ethereum для отправки (не более чем на балансе отправителя + расходы на газ) :")
            amount_wei = sender.w3.to_wei(amount_eth, 'ether')

            transaction = await sender.prepare_tx(recipient.address, amount_eth)

            gas = await quantity_check(sender, transaction)

            if not gas:
                continue
            break

        if eip_1559:
            gas_cost_wei = transaction['maxFeePerGas'] * gas
            gas_cost_eth = sender.w3.from_wei(gas_cost_wei, 'ether')
        else:
            gas_cost_wei = transaction['gasPrice'] * gas
            gas_cost_eth = sender.w3.from_wei(gas_cost_wei, 'ether')

        total_cost_wei = float(amount_wei) + gas_cost_wei

        logger.info(f"ℹ️ Будем отправлять {amount_eth} eth с кошелька {sender.address} на кошелек {recipient.address}")
        logger.info(f"ℹ️ {gas_cost_eth:.20f} eth плата за газ. ✅ Средств на кошельке достаточно для отправки. ✅ Средств достаточно для покрытия платы за газ.")

        if wait_until_confirm("📢 Подтвердите отправку средств (y/n): "):
            tx_hash = await sender.sign_and_send_tx(transaction)
            await sender.wait_tx(tx_hash)

            sender_balance_wei, sender_balance_eth = await update_balance(sender)
            recipient_balance_wei, recipient_balance_eth = await update_balance(recipient)

            logger.info(f"💰 Баланс отправителя: {sender_balance_eth:.5f} eth")
            logger.info(f"💰 Баланс получателя: {recipient_balance_eth:.5f} eth")
            logger.success(f"✅️ Успешно отправлено {amount_eth} eth с кошелька {sender.address} на кошелек {recipient.address}")
        else:
            logger.warning("️📢 Пользователь отказался от подтверждения транзакции.")


if __name__ == '__main__':
    asyncio.run(main())