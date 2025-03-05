from loguru import logger
from web3 import Web3, HTTPProvider
from config import config, Chains
from core.bot import Bot
from core.onchain import Onchain
from core.excel import Excel
from models.account import Account
from models.chain import Chain
from utils.logging import init_logger
from utils.utils import (random_sleep, get_accounts, select_profiles, get_user_agent)



def main():

    init_logger()
    accounts = get_accounts()
    accounts_for_work = select_profiles(accounts)

    for i in range(config.cycle):
        for account in accounts_for_work:
            worker(account)
            random_sleep(*config.pause_between_profile)
        logger.success(f'Цикл {i + 1} завершен! Обработано {len(accounts_for_work)} аккаунтов.')
        logger.info(f'Ожидание перед следующим циклом ~{config.pause_between_cycle[1]} секунд.')
        random_sleep(*config.pause_between_cycle)

def worker(account: Account) -> None:

    try:
        with Bot(account) as bot:
            activity(bot)
    except Exception as e:
        logger.critical(f"Ошибка при обработке аккаунта {account}: {e}")

def activity(bot: Bot):

    get_user_agent()
    excel_report = Excel(bot.account, file='MonadActivity.xlsx')
    excel_report.set_cell('Address', f'{bot.account.address}')
    excel_report.set_date('Date')

    try:
        onchain_instance = Onchain(bot.account, Chains.SONEIUM)
        onchain_instance.get_tx_count(address=bot.account.address)
        excel_report.increase_counter(f'Txs Count')
    except Exception as e:
        logger.error(f'Ошибка в сети {Chains.SONEIUM.name.upper()}: {e}')

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.warning('Программа завершена вручную!')