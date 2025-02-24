import random
import time
from loguru import logger
from config import config, Chains
from core.bot import Bot
from core.excel import Excel
from core.onchain import Onchain
from models.account import Account
from models.amount import Amount
from snippets.activities.relay import get_request_id, relay
from utils.inputs import input_pause, input_cycle_amount, input_cycle_pause
from utils.logging import init_logger
from utils.utils import (random_sleep, get_accounts, select_profiles)
from snippets import activities

def main():

    init_logger()
    accounts = get_accounts()
    accounts_for_work = select_profiles(accounts)
    pause = input_pause()
    cycle_amount = input_cycle_amount()
    cycle_pause = input_cycle_pause()
    for i in range(cycle_amount):
        for account in accounts_for_work:
            worker(account)
            random_sleep(pause)
        logger.success(f'Цикл {i + 1} завершен, обработано {len(accounts_for_work)} аккаунтов!')
        logger.info(f'Ожидание перед следующим циклом ~{config.pause_between_cycle[1]} секунд!')
        random_sleep(cycle_pause)

def worker(account: Account) -> None:

    try:
        with Bot(account) as bot:
            activity(bot)
    except Exception as e:
        logger.critical(f"{account.profile_number} Ошибка при инициализации Bot: {e}")

def activity(bot: Bot):

    excel_report = Excel(bot.account, file='SoneiumActivity.xlsx')
    excel_report.set_cell('Address', f'{bot.account.address}')
    excel_report.set_date('Date')
    bot.onchain.change_chain(Chains.SONEIUM)
    chains = [Chains.OP, Chains.BASE, Chains.ZKSYNC, Chains.ARBITRUM_ONE, Chains.UNICHAIN, Chains.LINEA]
    random_chains = random.sample(chains, 6)
    for to_chain in random_chains:
        amount = Amount(random.uniform(0.0001, 0.00015))
        if amount > bot.onchain.get_balance().ether:
            logger.error('Недостаточно средств для отправки транзакции! Переходим к другому профилю.')
            return
        relay(bot, to_chain=to_chain, amount=amount)
        excel_report.increase_counter(f'RELAY')
        random_sleep(10, 30)

    logger.success('Активность на RELAY прошла успешно! Данные записаны в таблицу SoneiumActivity.xlsx')

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.warning('Программа завершена вручную!')
