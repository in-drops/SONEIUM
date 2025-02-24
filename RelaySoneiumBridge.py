import random
from typing import Tuple
from loguru import logger
from config import config, Chains
from core.bot import Bot
from core.onchain import Onchain
from models.account import Account
from models.amount import Amount
from models.chain import Chain
from utils.inputs import input_deposit_amount, input_pause
from utils.logging import init_logger
from utils.utils import (random_sleep, get_accounts, select_profiles, get_user_agent)
import re
from snippets.activities.relay import relay

def input_withdraw_chain() -> Chain:

    input_chain_message = (
        f"Выбор сети вывода с каждого кошелька токена ЕТН для пополнения сети SONEIUM:\n"
        f"1 - ARBITRUM ONE\n"
        f"2 - BASE\n"
        f"3 - OPTIMISM\n"
    )
    while True:
        input_chain = input(f'{input_chain_message}Введите номер выбора и нажмите ENTER: ')
        input_chain = re.sub(r'\D', '', input_chain)

        if input_chain == '1':
            from_chain = Chains.ARBITRUM_ONE
            return from_chain

        if input_chain == '2':
            from_chain = Chains.BASE
            return from_chain

        if input_chain == '3':
            from_chain = Chains.OP
            return from_chain

        print("Некорректный ввод! Введите 1, 2 или 3.\n")

def input_to_chain_deposit() -> Tuple:

    from_chain = input_withdraw_chain()
    print(f'Выбрана сеть вывода {from_chain.name.upper()}!\n')
    amount_input = input_deposit_amount()
    print(f"Сумма хранения каждого кошелька в сети SONEIUM: {amount_input:.5f} {from_chain.native_token}!")
    pause = input_pause()
    return from_chain, amount_input, pause

def main():

    init_logger()
    accounts = get_accounts()
    accounts_for_work = select_profiles(accounts)

    for i in range(config.cycle):
        random.shuffle(accounts_for_work)
        from_chain, amount_input, pause = input_to_chain_deposit()
        for account in accounts_for_work:
            worker(account, from_chain, amount_input)
            random_sleep(pause)

        logger.success(f'Цикл {i + 1} завершен! Обработано {len(accounts_for_work)} аккаунтов!')
        logger.info(f'Ожидание перед следующим циклом ~{config.pause_between_cycle[1]} секунд!')
        random_sleep(pause)

def worker(account: Account, from_chain, amount_input) -> None:

    try:
        with Bot(account) as bot:
            activity(bot, from_chain, amount_input)
    except Exception as e:
        logger.critical(f"Ошибка при обработке аккаунта {account}: {e}")

def activity(bot: Bot, from_chain, amount_input):

    get_user_agent()
    bot.onchain.change_chain(from_chain)
    multiplier = random.uniform(1.01, 1.05)
    amount_input *= multiplier
    from_chain_balance = bot.onchain.get_balance().ether
    to_chain = Chains.SONEIUM
    to_chain_balance_before = Onchain(bot.account, to_chain).get_balance().ether
    deposit_amount = Amount(amount_input - to_chain_balance_before)

    if to_chain_balance_before > amount_input:
        logger.warning(
            f'Баланс в сети {to_chain.name.upper()}: {to_chain_balance_before:.5f} {to_chain.native_token}. Пополнение не требуется!')
        return

    if deposit_amount > from_chain_balance:
        logger.error(f'Баланс в сети {from_chain.name.upper()} недостаточный для перевода: {from_chain_balance:.5f} {from_chain_balance.native_token}!')
        return

    relay(bot, to_chain=to_chain, amount=deposit_amount)
    random_sleep(10, 20)

    for _ in range(60):
        to_chain_balance_after = Onchain(bot.account, to_chain).get_balance().ether
        if to_chain_balance_after > to_chain_balance_before:
            logger.success(
                f'Активность на RELAY прошла успешно! Обновлённый баланс в сети {to_chain.name.upper()}: {to_chain_balance_after:.5f} {to_chain.native_token}.')
        break
    else:
        logger.error('Транзакция не прошла!')
        raise Exception('Транзакция не прошла!')

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.warning('Программа завершена вручную!')